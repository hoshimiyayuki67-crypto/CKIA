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

class CampusPalette {
  const CampusPalette(this.dark);
  final bool dark;
  static CampusPalette of(BuildContext context) => CampusPalette(Theme.of(context).brightness == Brightness.dark);
  Color get ink => dark ? const Color(0xFFE3EFEA) : CampusColors.ink;
  Color get muted => dark ? const Color(0xFFA0B8AE) : CampusColors.muted;
  Color get green => dark ? const Color(0xFF7CDBB6) : CampusColors.green;
  Color get mint => dark ? const Color(0xFF1E3930) : CampusColors.mint;
  Color get canvas => dark ? const Color(0xFF0E1918) : CampusColors.canvas;
  Color get line => dark ? const Color(0xFF2E413B) : CampusColors.line;
}

ThemeData campusTheme([Brightness brightness = Brightness.light]) {
  final palette = CampusPalette(brightness == Brightness.dark);
  final dark = palette.dark;
  final surface = dark ? const Color(0xFF182622) : Colors.white;
  final scheme = ColorScheme.fromSeed(seedColor: CampusColors.green, brightness: brightness,
      surface: surface, primary: palette.green,
      onPrimary: dark ? const Color(0xFF10382C) : Colors.white);
  return ThemeData(
  useMaterial3: true,
  brightness: brightness,
  colorScheme: scheme,
  scaffoldBackgroundColor: palette.canvas,
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
  ).apply(bodyColor: palette.ink, displayColor: palette.ink),
  appBarTheme: AppBarTheme(
    backgroundColor: palette.canvas, surfaceTintColor: Colors.transparent,
    elevation: 0, toolbarHeight: 78, centerTitle: false,
    systemOverlayStyle: SystemUiOverlayStyle(
      statusBarColor: palette.canvas, statusBarIconBrightness: dark ? Brightness.light : Brightness.dark,
      systemNavigationBarColor: palette.canvas,
      systemNavigationBarIconBrightness: dark ? Brightness.light : Brightness.dark,
    ),
  ),
  filledButtonTheme: FilledButtonThemeData(style: FilledButton.styleFrom(
    backgroundColor: scheme.primary, foregroundColor: scheme.onPrimary,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
  )),
  inputDecorationTheme: InputDecorationTheme(
    filled: true, fillColor: dark ? const Color(0xFF20332B) : const Color(0xFFF1F6F2),
    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
    focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16),
        borderSide: BorderSide(color: palette.green)),
  ),
  bottomSheetTheme: BottomSheetThemeData(backgroundColor: surface,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(28)))),
  expansionTileTheme: const ExpansionTileThemeData(tilePadding: EdgeInsets.zero,
    childrenPadding: EdgeInsets.only(bottom: 12), shape: Border(), collapsedShape: Border()),
  chipTheme: ChipThemeData(
    side: BorderSide(color: palette.line), backgroundColor: surface,
    selectedColor: palette.mint,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
    labelStyle: TextStyle(fontFamily: 'CampusSans', fontSize: 13,
        color: palette.ink), showCheckmark: false,
  ),
  snackBarTheme: SnackBarThemeData(behavior: SnackBarBehavior.floating,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14))),
  );
}

class CampusMark extends StatelessWidget {
  const CampusMark({super.key, this.size = 44});
  final double size;
  @override
  Widget build(BuildContext context) => Semantics(label: '校园万事通标志',
      child: SizedBox(width: size, height: size, child: CustomPaint(painter: _CampusMarkPainter())));
}

class _CampusMarkPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    canvas.save(); canvas.scale(size.width / 108, size.height / 108);
    final background = Paint()..shader = const LinearGradient(
      colors: [Color(0xFF124F55), Color(0xFF238775)],
      begin: Alignment.topLeft, end: Alignment.bottomRight).createShader(const Rect.fromLTWH(0, 0, 108, 108));
    canvas.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(0, 0, 108, 108), const Radius.circular(30)), background);
    canvas.drawCircle(const Offset(80, 25), 28, Paint()..color = const Color(0x187CE7C1));
    final left = Path()..moveTo(24, 35)..quadraticBezierTo(39, 29, 52, 39)
      ..lineTo(52, 79)..quadraticBezierTo(39, 69, 24, 75)..close();
    final right = Path()..moveTo(56, 39)..quadraticBezierTo(69, 29, 84, 35)
      ..lineTo(84, 75)..quadraticBezierTo(69, 69, 56, 79)..close();
    canvas.drawPath(left, Paint()..color = const Color(0xFFE8F8EF));
    canvas.drawPath(right, Paint()..color = const Color(0xFF9BE7CB));
    final lines = Paint()..color = const Color(0xFF348C78)..strokeWidth = 3..strokeCap = StrokeCap.round;
    canvas.drawLine(const Offset(32, 46), const Offset(44, 49), lines);
    canvas.drawLine(const Offset(32, 56), const Offset(44, 59), lines);
    canvas.drawLine(const Offset(32, 66), const Offset(41, 68), lines);
    final needle = Path()..moveTo(64, 64)..lineTo(71, 46)..lineTo(78, 64)..lineTo(71, 60)..close();
    canvas.drawPath(needle, Paint()..color = const Color(0xFF145B58));
    final spark = Path()..moveTo(80, 16)..lineTo(83, 23)..lineTo(90, 26)
      ..lineTo(83, 29)..lineTo(80, 36)..lineTo(77, 29)..lineTo(70, 26)..lineTo(77, 23)..close();
    canvas.drawPath(spark, Paint()..color = const Color(0xFFF4D78B));
    canvas.restore();
  }
  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
