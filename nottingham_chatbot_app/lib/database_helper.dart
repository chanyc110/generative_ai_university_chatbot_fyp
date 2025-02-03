import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'dart:convert';
import 'package:crypto/crypto.dart';

class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._init();
  static Database? _database;

  DatabaseHelper._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('users.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(path, version: 1, onCreate: _createDB);
  }

  Future<void> _createDB(Database db, int version) async {
    await db.execute('''
      CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
      )
    ''');
  }

  Future<int> registerUser(String username, String password) async {
    final db = await instance.database;
    final hashedPassword = _hashPassword(password);
    try {
    return await db.insert(
      'users',
      {'username': username, 'password': hashedPassword},
      conflictAlgorithm: ConflictAlgorithm.fail, // Prevent duplicate usernames
    );
    } catch (e) {
      throw Exception('Username already exists'); // Handle duplicate users
    }
  }

  Future<bool> authenticateUser(String username, String password) async {
    final db = await instance.database;
    final hashedPassword = _hashPassword(password);

    final result = await db.query(
      'users',
      where: 'username = ? AND password = ?',
      whereArgs: [username, hashedPassword],
    );

    return result.isNotEmpty;
  }

  String _hashPassword(String password) {
    final bytes = utf8.encode(password);
    final digest = sha256.convert(bytes);
    return digest.toString();
  }
}
