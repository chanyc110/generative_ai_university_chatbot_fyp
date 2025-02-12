import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_markdown/flutter_markdown.dart';
import 'webview_page.dart';



class ChatHistory {
  static List<Map<String, String>> messages = [];
  static List<String> chatNames = ["Chat 1"];
  static List<List<Map<String, String>>> chatHistories = [[]];
}

class ChatbotPage extends StatefulWidget {
  final List<Map<String, String>> messages;

  ChatbotPage({required this.messages});

  @override
  _ChatbotPageState createState() => _ChatbotPageState();
}

class _ChatbotPageState extends State<ChatbotPage> {
  final TextEditingController _queryController = TextEditingController();
  late List<Map<String, String>> _messages; // Store messages
  bool _isLoading = false;
  int _selectedChatIndex = 0;

  @override
  void initState() {
    super.initState();
    _messages = List.from(widget.messages);
  }

  void _switchChat(int index) {
    setState(() {
      _selectedChatIndex = index;
      _messages = List.from(ChatHistory.chatHistories[index]);
    });
  }

  void _addNewChat() {
    setState(() {
      ChatHistory.chatNames.add("Chat ${ChatHistory.chatNames.length + 1}");
      ChatHistory.chatHistories.add([]);
    });
    Navigator.pop(context); // Close the previous sidebar
    _showSidebar();
  }

  void _showSidebar() {
    showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setState) {
            return Align(
              alignment: Alignment.centerRight,
              child: FractionallySizedBox(
                widthFactor: 0.5,
                child: Material(
                  color: Colors.white,
                  elevation: 8,
                  child: Column(
                    children: [
                      Expanded(
                        child: ListView.builder(
                          itemCount: ChatHistory.chatNames.length,
                          itemBuilder: (context, index) {
                            return ListTile(
                              title: Text(ChatHistory.chatNames[index]),
                              onTap: () {
                                Navigator.pop(context);
                                _switchChat(index);
                              },
                              trailing: IconButton(
                                icon: Icon(Icons.edit),
                                onPressed: () {
                                  _renameChat(index, setState);
                                },
                              ),
                            );
                          },
                        ),
                      ),
                  Divider(),
                  Padding(
                    padding: const EdgeInsets.all(8.0),
                    child: ElevatedButton(
                      onPressed: _addNewChat,
                      child: Text('Add New Chat'),
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.all(8.0),
                    child: ElevatedButton(
                      onPressed: () {
                        Navigator.pop(context);
                      },
                      child: Text('Close'),
                      ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        );
      },
    );
  }

  Future<void> _renameChat(int index, void Function(void Function()) setSidebarState) async {
    TextEditingController renameController = TextEditingController();
    await showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text('Rename Chat'),
          content: TextField(
            controller: renameController,
            decoration: InputDecoration(hintText: 'Enter new chat name'),
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
              },
              child: Text('Cancel'),
            ),
            TextButton(
              onPressed: () {
                setState(() {
                  ChatHistory.chatNames[index] = renameController.text.isNotEmpty
                      ? renameController.text
                      : ChatHistory.chatNames[index];
                });
                setSidebarState(() {});
                Navigator.of(context).pop();
              },
              child: Text('Save'),
            ),
          ],
        );
      },
    );
  }

  Future<void> _sendMessage() async {
    if (_isLoading) return; // Prevent duplicate requests

    final userQuery = _queryController.text.trim();
    if (userQuery.isEmpty) return;

    // Add user's query to the chat
    setState(() {
      _messages.add({"sender": "user", "message": userQuery});
      _isLoading = true;
    });
    _queryController.clear();

    try{
      // Simulate sending a request to the API
      final response = await _fetchChatbotResponse(userQuery);
      // Add chatbot's response to the chat
      setState(() {
        _messages.add({"sender": "bot", "message": response});
      });

      // Update shared history only once at the end
      ChatHistory.chatHistories[_selectedChatIndex] = List.from(_messages);
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<String> _fetchChatbotResponse(String userQuery) async {
    const String apiUrl = 'http://10.0.2.2:8000/chat';
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
        title: Text('Chatbot'),
        actions: [
          IconButton(
            icon: Icon(Icons.menu),
            onPressed:   _showSidebar,
            ),
        ],
      ),
      body: Column(
        children: [
        Container(
            padding: EdgeInsets.symmetric(vertical: 10),
            child: Center(
              child: Text(
                ChatHistory.chatNames[_selectedChatIndex],
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ),
          ),
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
                        child:MarkdownBody(
                          data: message["message"] ?? "",
                          selectable: true,  // Allows users to select and copy text
                          onTapLink: (text, href, title) async {
                            if (href != null) {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => WebViewPage(url: href),
                                ),
                              );
                            }
                          },
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
                  Text("Typing...")
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
                      hintText: "Ask a question...",
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                  ),
                ),
                SizedBox(width: 8),
                IconButton(
                  icon: Icon(Icons.send, color: Colors.blue),
                  onPressed: _isLoading ? null : _sendMessage, // Disable while loading
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

}