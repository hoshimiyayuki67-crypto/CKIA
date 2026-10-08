import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class CampusColors {
  static const ink = Color(0xFF173A35);
  static const muted = Color(0xFF6F827D);
  static const green = Color(0xFF257E67);
  static const mint = Color(0xFFE8F4EC);
  static const canvas = Color(0xFFF6F8F3);
  static const line = Color(0xFFE2EAE2);
}

ThemeData campusTheme() => ThemeData(
  useMaterial3: true,
  colorScheme: ColorScheme.fromSeed(seedColor: CampusColors.green, surface: Colors.white),
  scaffoldBackgroundColor: CampusColors.canvas,
  fontFamily: 'CampusSans',
  fontFamilyFallback: const ['Noto Sans CJK SC', 'sans-serif'],
  textTheme: const TextTheme(
    headlineMedium: TextStyle(fontSize: 30, height: 1.35, fontWeight: FontWeight.w700),
    titleLarge: TextStyle(fontSize: 21, height: 1.4, fontWeight: FontWeight.w700),
    titleMedium: TextStyle(fontSize: 16, height: 1.4, fontWeight: FontWeight.w600),
    bodyLarge: TextStyle(fontSize: 15, height: 1.65),
    bodyMedium: TextStyle(fontSize: 14, height: 1.6),
    bodySmall: TextStyle(fontSize: 12, height: 1.5),
    labelSmall: TextStyle(fontSize: 11, height: 1.4, fontWeight: FontWeight.w500),
  ).apply(bodyColor: CampusColors.ink, displayColor: CampusColors.ink),
  appBarTheme: const AppBarTheme(
    backgroundColor: CampusColors.canvas, surfaceTintColor: Colors.transparent,
    elevation: 0, toolbarHeight: 78, centerTitle: false,
    systemOverlayStyle: SystemUiOverlayStyle(
      statusBarColor: CampusColors.canvas, statusBarIconBrightness: Brightness.dark,
      systemNavigationBarColor: CampusColors.canvas,
      systemNavigationBarIconBrightness: Brightness.dark,
    ),
  ),
  filledButtonTheme: FilledButtonThemeData(style: FilledButton.styleFrom(
    backgroundColor: CampusColors.green,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
  )),
  chipTheme: ChipThemeData(
    side: const BorderSide(color: CampusColors.line), backgroundColor: Colors.white,
    selectedColor: CampusColors.mint,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
    labelStyle: const TextStyle(fontSize: 13, color: CampusColors.ink), showCheckmark: false,
  ),
  snackBarTheme: SnackBarThemeData(behavior: SnackBarBehavior.floating,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14))),
);

class CampusMark extends StatelessWidget {
  const CampusMark({super.key, this.size = 44});
  final double size;
  @override
  Widget build(BuildContext context) => Container(
    width: size, height: size,
    decoration: BoxDecoration(color: CampusColors.green,
        borderRadius: BorderRadius.circular(size * .32)),
    child: Icon(Icons.school_rounded, size: size * .56, color: Colors.white),
  );
}
