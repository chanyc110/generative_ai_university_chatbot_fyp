import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:intl/intl.dart';
import 'package:http/http.dart' as http;
import 'package:timezone/data/latest_all.dart' as tz;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';


class ReminderPage extends StatefulWidget {
  @override
  _ReminderPageState createState() => _ReminderPageState();
}

class _ReminderPageState extends State<ReminderPage> {
  final TextEditingController _queryController = TextEditingController();
  bool _isLoading = false;
  List<Map<String, String>> _messages = [];
  FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin = FlutterLocalNotificationsPlugin();

  @override
  void initState() {
    super.initState();
    _initializeNotifications();
    tz.initializeTimeZones();
    _restoreReminders();
  }

  Future<void> _restoreReminders() async {
  List<Map<String, dynamic>> savedReminders = await _loadReminders();
  
  for (var reminder in savedReminders) {
    String title = reminder['title'];
    DateTime dateTime = DateTime.parse(reminder['dateTime']);
    int remindBeforeMinutes = reminder['remindBefore'];

    // Re-schedule each reminder
    await _scheduleNotification(title, dateTime, remindBeforeMinutes);
  }
}

  Future<void> _initializeNotifications() async {
    const AndroidInitializationSettings androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');

    final AndroidNotificationChannel channel = AndroidNotificationChannel(
    'reminder_channel', // ✅ Make sure this matches your scheduled notification channel
    'Reminders',
    description: 'Channel for reminder notifications',
    importance: Importance.high,
    );

    final AndroidFlutterLocalNotificationsPlugin? androidImplementation =
        flutterLocalNotificationsPlugin.resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>();

    await androidImplementation?.createNotificationChannel(channel);

    final InitializationSettings initSettings = InitializationSettings(android: androidSettings);
    await flutterLocalNotificationsPlugin.initialize(
      initSettings,
      onDidReceiveNotificationResponse: (NotificationResponse response) async {
        print("🔔 Notification Clicked: ${response.payload}");
      },
    );

    await flutterLocalNotificationsPlugin.resolvePlatformSpecificImplementation<
      AndroidFlutterLocalNotificationsPlugin>()?.requestNotificationsPermission();
  }

  Future<void> _sendMessage() async {
    String userQuery = _queryController.text.trim();
    if (userQuery.isEmpty) return;

    setState(() {
      _messages.add({"sender": "user", "message": userQuery});
      _isLoading = true;
    });

    // Extract reminder details using GPT-4o
    Map<String, dynamic>? reminderDetails = await _extractReminderDetails(userQuery);

    if (reminderDetails == null) {
      setState(() {
        _messages.add({"sender": "bot", "message": "I couldn't process the reminder. Try again!"});
        _isLoading = false;
      });
      return;
    }

    String title = reminderDetails['title'];
    DateTime dateTime = DateTime.parse(reminderDetails['dateTime']);
    int remindBeforeMinutes = reminderDetails['remindBefore'];

    // Store Reminder Persistently
    await _saveReminder(title, dateTime, remindBeforeMinutes);

    // Schedule the reminder notification
    await _scheduleNotification(title, dateTime, remindBeforeMinutes);

    setState(() {
      _messages.add({
        "sender": "bot",
        "message": "✅ Reminder set for: **$title** on ${DateFormat('yyyy-MM-dd HH:mm').format(dateTime)}.\n\nI'll remind you **$remindBeforeMinutes minutes before**."
      });
      _isLoading = false;
    });

    _queryController.clear();
  }

  Future<Map<String, dynamic>?> _extractReminderDetails(String userQuery) async {
    String gpt4oApiKey = dotenv.env['OPENAI_API_KEY'] ?? "API_KEY_NOT_FOUND";
    String formattedDate = DateFormat('yyyy-MM-dd').format(DateTime.now());

    final List<Map<String, dynamic>> messages = [
    {
      'role': 'system',
      'content': "You are an AI that extracts structured reminder details from user messages. Today's date is $formattedDate.\n\n"
          "Extract the details in **this JSON format**:\n"
          "{\n"
          '  "title": "Meeting",\n'
          '  "dateTime": "2025-02-05T15:00:00",\n'
          '  "remindBefore": 15\n'
          "}\n\n"
          "**User request:** \"$userQuery\""
    },
    {
      'role': 'user',
      'content': userQuery
    }
  ];

    final response = await http.post(
      Uri.parse('https://api.openai.com/v1/chat/completions'),
      headers: {
        'Authorization': 'Bearer $gpt4oApiKey',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'model': 'gpt-4o-mini',
        'messages': messages,
        'max_tokens': 150
      }),
    );

    print("API Response Status: ${response.statusCode}");
    print("API Response Body: ${response.body}");

    if (response.statusCode == 200) {
      try{
      final jsonResponse = json.decode(response.body);
      final extractedData = json.decode(jsonResponse['choices'][0]['message']['content']);
      return extractedData;
    } catch (e) {
      print("Error parsing API response: $e");
      return null;
    }
  } else {
    print("API request failed. Response: ${response.body}");
    return null;
  }
  }

  Future<void> _saveReminder(String title, DateTime dateTime, int remindBeforeMinutes) async {
  SharedPreferences prefs = await SharedPreferences.getInstance();
  List<String>? reminders = prefs.getStringList('reminders') ?? [];

  // ✅ Cancel previous notification for this title
  int notificationId = title.hashCode;
  await flutterLocalNotificationsPlugin.cancel(notificationId);

  Map<String, dynamic> newReminder = {
    'title': title,
    'dateTime': dateTime.toIso8601String(),
    'remindBefore': remindBeforeMinutes
  };

  reminders.add(jsonEncode(newReminder));
  await prefs.setStringList('reminders', reminders);

  print("✅ Reminder Saved: $title at ${dateTime.toLocal()}");
}

Future<List<Map<String, dynamic>>> _loadReminders() async {
  SharedPreferences prefs = await SharedPreferences.getInstance();
  List<String>? reminders = prefs.getStringList('reminders') ?? [];
  
  DateTime now = DateTime.now();

  print("⏳ Current Time: ${now.toLocal()}");
  
  List<Map<String, dynamic>> validReminders = [];
  List<String> updatedReminders = [];

  for (String r in reminders) {
    Map<String, dynamic> reminder = jsonDecode(r);
    DateTime reminderTime = DateTime.parse(reminder['dateTime']).toLocal(); // ✅ Convert reminder time to local

    if (reminderTime.isAfter(now)) {
      validReminders.add(reminder);
      updatedReminders.add(jsonEncode(reminder)); // ✅ Keep valid reminders
    } else {
      int notificationId = reminder['title'].hashCode;
      await flutterLocalNotificationsPlugin.cancel(notificationId);
      print("🗑 Expired reminder removed: ${reminder['title']} at $reminderTime ");
    }
  }

  await prefs.setStringList('reminders', updatedReminders); // ✅ Save only valid reminders

  print("📌 Final Loaded Reminders: $validReminders");
  return validReminders;
}

  Future<void> _scheduleNotification(String title, DateTime dateTime, int remindBeforeMinutes) async {
    DateTime notifyTime = dateTime.subtract(Duration(minutes: remindBeforeMinutes));

    print("🔍 Checking Notification Time:");
    print("   - Current Time: ${DateTime.now().toLocal()}");
    print("   - Notification Time: ${notifyTime.toLocal()}");

    if (notifyTime.isAfter(DateTime.now())) {
      try{
      AndroidNotificationDetails androidDetails = const AndroidNotificationDetails(
        'reminder_channel',
        'Reminders',
        importance: Importance.high,
        priority: Priority.high,
        playSound: true,
        enableVibration: true,
      );
      NotificationDetails platformDetails = NotificationDetails(android: androidDetails);

      print("✅ Scheduling Notification: $title at $notifyTime"); // log

      Future.delayed(notifyTime.difference(DateTime.now()), () async {
        await flutterLocalNotificationsPlugin.show(
          title.hashCode,
          'Reminder',
          title,
          platformDetails,
        );

        print("🔔 Reminder Triggered: $title");
      });

    } catch (e) {
      print("❌ Error scheduling notification: $e");
    }
  } else {
    print("⏳ Cannot schedule notification in the past!");
  }
  }

  Future<void> _testNotification() async {
  AndroidNotificationDetails androidDetails = const AndroidNotificationDetails(
    'test_channel',  // ✅ Make sure this matches an existing notification channel ID
    'Test Notifications',
    importance: Importance.high,
    priority: Priority.high,
    playSound: true, // ✅ Ensure sound is enabled
    enableVibration: true, // ✅ Enable vibration
  );
  
  NotificationDetails platformDetails = NotificationDetails(android: androidDetails);

  await flutterLocalNotificationsPlugin.show(
    999, // Unique ID
    '🚀 Test Notification',
    'This is a test notification!',
    platformDetails,
  );

  print("✅ Test Notification Sent!");
}


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Reminders')),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                final isUser = message["sender"] == "user";
                return Row(
                  mainAxisAlignment:
                      isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
                  children: [
                    if (!isUser)
                      CircleAvatar(
                        child: Icon(Icons.smart_toy),
                        backgroundColor: Colors.grey[300],
                      ),
                    Flexible(
                      child: Container(
                        margin: EdgeInsets.symmetric(vertical: 5, horizontal: 10),
                        padding: EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: isUser ? Colors.blue[100] : Colors.grey[300],
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          message["message"] ?? "",
                          style: TextStyle(fontSize: 16),
                        ),
                      ),
                    ),
                    if (isUser)
                      CircleAvatar(
                        child: Icon(Icons.person),
                        backgroundColor: Colors.blue[100],
                      ),
                  ],
                );
              },
            ),
          ),
          if (_isLoading)
            Padding(
              padding: const EdgeInsets.all(8.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(width: 10),
                  Text("Processing..."),
                ],
              ),
            ),
          Divider(height: 1),

           // ✅ Test Notification Button
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: ElevatedButton.icon(
              onPressed: _testNotification, // ✅ Calls test function
              icon: Icon(Icons.notifications_active),
              label: Text("Test Notification"),
              style: ElevatedButton.styleFrom(
                padding: EdgeInsets.symmetric(vertical: 10, horizontal: 20),
                textStyle: TextStyle(fontSize: 16),
              ),
            ),
          ),

          Container(
            padding: EdgeInsets.symmetric(horizontal: 8, vertical: 5),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _queryController,
                    decoration: InputDecoration(
                      hintText: "Set a reminder...",
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(20),
                      ),
                    ),
                  ),
                ),
                SizedBox(width: 8),
                IconButton(
                  icon: Icon(Icons.send, color: Colors.blue),
                  onPressed: _isLoading ? null : _sendMessage,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

