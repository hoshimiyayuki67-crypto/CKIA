import 'package:flutter/material.dart';

void main() => runApp(const CampusApp());

class CampusApp extends StatelessWidget {
  const CampusApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '校园万事通',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(useMaterial3: true, colorSchemeSeed: Colors.teal),
      home: Scaffold(
        appBar: AppBar(title: const Text('校园万事通')),
        body: const Padding(
          padding: EdgeInsets.all(24),
          child: Text('开发准备中\n\n知识库尚未接入，暂无法核实学校办事规定。'),
        ),
      ),
    );
  }
}
