import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

class SportsChatHistory {
  static List<Map<String, String>> messages = [];
}

class SportsComplexPage extends StatefulWidget {
  @override
  _SportsComplexPageState createState() => _SportsComplexPageState();
}

class _SportsComplexPageState extends State<SportsComplexPage> {
  final TextEditingController _queryController = TextEditingController();
  List<Map<String, String>> _messages = [];
  bool _isLoading = false;

  // Booking fields and steps
  Map<String, String> _bookingDetails = {};
  int _currentStep = -1; // -1 means not in booking flow

  final List<String> _bookingSteps = [
    "username",
    "password",
    "venue",
    "contact_no",
    "purpose",
    "date",
    "session"
  ];

  final Map<String, String> _venueOptions = {
    "Gymnasium": "45419910-a0000040-5b1ba29c-fcac248d",
    "Swimming Pool": "58e58998-a0000040-1455f332-fa3a484b"
  };

  final Map<String, String> _sessionOptions = {
    "9-10": "c6d16693-a0000040-615864a2-402fab7d",
    "5-6": "ee0108db-a0000040-6172fc20-ad779c80"
  };

  @override
  void initState() {
    super.initState();
    _loadChatHistory();
  }

  void _loadChatHistory() {
    setState(() {
      _messages = List.from(SportsChatHistory.messages);
      if (_messages.isEmpty) {
        _addBotMessage("Welcome! To start a new booking, please type 'new booking'."); // initial bot message
      }
    });
  }

  Future<void> _sendMessage() async {
    if (_isLoading) return;

    final userQuery = _queryController.text.trim();
    if (userQuery.isEmpty) return;

    setState(() {
      _messages.add({"sender": "user", "message": userQuery});
      SportsChatHistory.messages.add({"sender": "user", "message": userQuery});
      _isLoading = true;
    });
    _queryController.clear();

    if (userQuery.toLowerCase() == "new booking") {
      _startBookingProcess();
      return;
    }

    if (_currentStep >= 0) {
      _processBookingStep(userQuery);
      return;
    }

    try {
      final response = await _fetchChatbotResponse(userQuery);
      _addBotMessage(response);
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _startBookingProcess() {
    setState(() {
      _bookingDetails.clear();
      _currentStep = 0;
      _addBotMessage("Let's start your booking! Please enter your username.");
      _isLoading = false;
    });
  }

    void _processBookingStep(String userResponse) {
    if (_currentStep < _bookingSteps.length) {
      String currentField = _bookingSteps[_currentStep];
      _bookingDetails[currentField] = userResponse;
      _currentStep++;

      if (_currentStep < _bookingSteps.length) {
        _askForNextStep();
      } else {
        _finalizeBooking();
      }
    }
  }

  void _askForNextStep() {
    String nextField = _bookingSteps[_currentStep];

    if (nextField == "venue") {
      _showRadioOptions("Please select a venue:", _venueOptions);
    } else if (nextField == "session") {
      _showRadioOptions("Please select a session:", _sessionOptions);
    } else if (nextField == "date") {
    _showDatePicker();
    } 
    else {
      _addBotMessage("Please enter your $nextField.");
    }

    setState(() => _isLoading = false);
  }

  void _showDatePicker() async {
  DateTime? pickedDate = await showDatePicker(
    context: context,
    initialDate: DateTime.now(),
    firstDate: DateTime.now(),
    lastDate: DateTime(2026),
  );

  if (pickedDate != null) {
    String formattedDate = _formatDate(pickedDate);

    setState(() {
      _bookingDetails["date"] = formattedDate;
    });

    _addBotMessage("Selected Date: $formattedDate");
    _currentStep++; 
    _askForNextStep();  // Move to the next step
  } else {
    _addBotMessage("No date selected. Please pick a date.");
  }
}

String _formatDate(DateTime date) {
  return "${_getDayOfWeek(date.weekday)}, ${date.day}-${_getMonth(date.month)}-${date.year}";
}

String _getDayOfWeek(int weekday) {
  switch (weekday) {
    case 1:
      return "Mon";
    case 2:
      return "Tue";
    case 3:
      return "Wed";
    case 4:
      return "Thu";
    case 5:
      return "Fri";
    case 6:
      return "Sat";
    case 7:
      return "Sun";
    default:
      return "";
  }
}

String _getMonth(int month) {
  switch (month) {
    case 1:
      return "January";
    case 2:
      return "February";
    case 3:
      return "March";
    case 4:
      return "April";
    case 5:
      return "May";
    case 6:
      return "June";
    case 7:
      return "July";
    case 8:
      return "August";
    case 9:
      return "September";
    case 10:
      return "October";
    case 11:
      return "November";
    case 12:
      return "December";
    default:
      return "";
  }
}

  void _showRadioOptions(String message, Map<String, String> options) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text(message),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: options.entries.map((entry) {
              return ListTile(
                title: Text(entry.key),
                leading: Radio<String>(
                  value: entry.value,
                  groupValue: _bookingDetails[_bookingSteps[_currentStep]],
                  onChanged: (value) {
                    setState(() {
                      _bookingDetails[_bookingSteps[_currentStep]] = value!;
                      Navigator.pop(context);
                      _processBookingStep(value);
                    });
                  },
                ),
              );
            }).toList(),
          ),
        );
      },
    );
  }

  void _finalizeBooking() async {
    _addBotMessage("Processing your booking...");

    try {
      final response = await http.post(
        Uri.parse('http://10.0.2.2:8000/make_booking'),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(_bookingDetails),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _addBotMessage(data["response"] ?? "Your booking has been confirmed!");
      } else {
        _addBotMessage("Error: Unable to confirm booking.");
      }
    } catch (e) {
      _addBotMessage("Error: $e");
    } finally {
      setState(() {
        _isLoading = false;
        _currentStep = -1;
      });
    }
  }

  Future<String> _fetchChatbotResponse(String userQuery) async {
    const String apiUrl = 'http://10.0.2.2:8000/make_booking';
    try {
      final response = await http.post(
        Uri.parse(apiUrl),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"user_query": userQuery}),
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data["response"] ?? "Sorry, I couldn't understand that.";
      } else {
        return "Error: Unable to fetch response.";
      }
    } catch (e) {
      return "Error: $e";
    }
  }

void _addBotMessage(String message) {
    setState(() {
      _messages.add({"sender": "bot", "message": message});
      SportsChatHistory.messages.add({"sender": "bot", "message": message});
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Sports Complex Booking'),
      ),
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
                  Text("Processing...")
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
                      hintText: "Make a booking...",
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


