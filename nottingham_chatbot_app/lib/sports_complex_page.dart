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

  @override
  void initState() {
    super.initState();
    _loadChatHistory();
  }

  void _loadChatHistory() {
    setState(() {
      _messages = List.from(SportsChatHistory.messages);
      if (_messages.isEmpty) {
      // Initial bot message when the chat opens
      final initialBotMessage = {
        "sender": "bot",
        "message": "Welcome! To start a new booking, please type 'new booking'."
      };
      _messages.add(initialBotMessage);
      SportsChatHistory.messages.add(initialBotMessage);
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

    try {
      final response = await _fetchChatbotResponse(userQuery);
      setState(() {
        _messages.add({"sender": "bot", "message": response});
        SportsChatHistory.messages.add({"sender": "bot", "message": response});
      });
    } finally {
      setState(() {
        _isLoading = false;
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


