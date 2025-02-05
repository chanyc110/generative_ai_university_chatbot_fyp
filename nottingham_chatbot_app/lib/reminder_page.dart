import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:intl/intl.dart';
import 'package:http/http.dart' as http;
import 'package:timezone/data/latest_all.dart' as tz;
import 'package:timezone/timezone.dart' as tz;
import 'package:shared_preferences/shared_preferences.dart';


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
    const InitializationSettings initSettings = InitializationSettings(android: androidSettings);
    await flutterLocalNotificationsPlugin.initialize(initSettings);
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
    String gpt4oApiKey = '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';
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

  Map<String, dynamic> newReminder = {
    'title': title,
    'dateTime': dateTime.toIso8601String(),
    'remindBefore': remindBeforeMinutes
  };

  reminders.add(jsonEncode(newReminder));
  await prefs.setStringList('reminders', reminders);
}

Future<List<Map<String, dynamic>>> _loadReminders() async {
  SharedPreferences prefs = await SharedPreferences.getInstance();
  List<String>? reminders = prefs.getStringList('reminders') ?? [];
  
  DateTime now = DateTime.now();

  print("⏳ Current Time: ${now.toIso8601String()}");
  
  List<Map<String, dynamic>> validReminders = [];
  List<String> updatedReminders = [];

  for (String r in reminders) {
    Map<String, dynamic> reminder = jsonDecode(r);
    DateTime reminderTime = DateTime.parse(reminder['dateTime']); // ✅ Convert reminder time to local

    if (reminderTime.isAfter(now)) {
      validReminders.add(reminder);
      updatedReminders.add(jsonEncode(reminder)); // ✅ Keep valid reminders
    } else {
      print("🗑 Expired reminder removed: ${reminder['title']} at $reminderTime ");
    }
  }

  await prefs.setStringList('reminders', updatedReminders); // ✅ Save only valid reminders

  print("📌 Final Loaded Reminders: $validReminders");
  return validReminders;
}

  Future<void> _scheduleNotification(String title, DateTime dateTime, int remindBeforeMinutes) async {
    DateTime notifyTime = dateTime.subtract(Duration(minutes: remindBeforeMinutes));

    if (notifyTime.isAfter(DateTime.now())) {
      try{
      AndroidNotificationDetails androidDetails = const AndroidNotificationDetails(
        'reminder_channel',
        'Reminders',
        importance: Importance.high,
        priority: Priority.high,
      );
      NotificationDetails platformDetails = NotificationDetails(android: androidDetails);

      print("✅ Scheduling Notification: $title at $notifyTime"); // log

      await flutterLocalNotificationsPlugin.zonedSchedule(
        title.hashCode,
        'Reminder',
        title,
        tz.TZDateTime.from(notifyTime, tz.local),
        platformDetails,
        androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
        matchDateTimeComponents: DateTimeComponents.time,
        uiLocalNotificationDateInterpretation: UILocalNotificationDateInterpretation.absoluteTime,
      );

      // Remove reminder after notification
      Future.delayed(Duration(minutes: remindBeforeMinutes + 1), () {
        setState(() {
          _messages.removeWhere((msg) => msg["message"]?.contains(title) ?? false);
        });
      });
    } catch (e) {
      print("❌ Error scheduling notification: $e");
    }
  } else {
    print("⏳ Cannot schedule notification in the past!");
  }
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

