import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class DBHelper {
  static Database? _database;

  static Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB();
    return _database!;
  }

  static Future<Database> _initDB() async {
    final path = join(await getDatabasesPath(), 'chatbot.db');
    return openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
          )
        ''');

        await db.execute('''
          CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            sender TEXT,
            message TEXT,
            FOREIGN KEY(chat_id) REFERENCES chats(id) ON DELETE CASCADE
          )
        ''');
      },
    );
  }

  // Add a new chat
  static Future<int> addChat(String name) async {
    final db = await database;
    return await db.insert('chats', {'name': name});
  }

  // Fetch all chats
  static Future<List<Map<String, dynamic>>> getChats() async {
    final db = await database;
    return await db.query('chats');
  }

  // Rename a chat
  static Future<void> renameChat(int id, String newName) async {
    final db = await database;
    await db.update('chats', {'name': newName}, where: 'id = ?', whereArgs: [id]);
  }

  // Delete a chat
  static Future<void> deleteChat(int id) async {
    final db = await database;
    await db.delete('chats', where: 'id = ?', whereArgs: [id]);
    await db.delete('messages', where: 'chat_id = ?', whereArgs: [id]);
  }

  // Add message
  static Future<void> addMessage(int chatId, String sender, String message) async {
    final db = await database;
    await db.insert('messages', {
      'chat_id': chatId,
      'sender': sender,
      'message': message,
    });
  }

  // Fetch messages for a chat
  static Future<List<Map<String, dynamic>>> getMessages(int chatId) async {
    final db = await database;
    return await db.query('messages', where: 'chat_id = ?', whereArgs: [chatId]);
  }
}


