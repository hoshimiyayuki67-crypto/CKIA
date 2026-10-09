import 'package:flutter/material.dart';

Duration motionDuration(BuildContext context, int milliseconds) =>
    MediaQuery.disableAnimationsOf(context) ? Duration.zero : Duration(milliseconds: milliseconds);

class Reveal extends StatelessWidget {
  const Reveal({super.key, required this.child});
  final Widget child;
  @override
  Widget build(BuildContext context) => TweenAnimationBuilder<double>(
    tween: Tween(begin: 0, end: 1), duration: motionDuration(context, 360),
    curve: Curves.easeOutCubic, child: child,
    builder: (context, value, child) => Opacity(opacity: value,
        child: Transform.translate(offset: Offset(0, 14 * (1 - value)), child: child)),
  );
}

class SearchPulse extends StatefulWidget {
  const SearchPulse({super.key, required this.searching});
  final bool searching;
  @override
  State<SearchPulse> createState() => _SearchPulseState();
}

class _SearchPulseState extends State<SearchPulse> with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 1100));
  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (MediaQuery.disableAnimationsOf(context)) { _controller.stop(); }
    else { _controller.repeat(reverse: true); }
  }
  @override
  void dispose() { _controller.dispose(); super.dispose(); }
  @override
  Widget build(BuildContext context) => Semantics(liveRegion: true,
    child: AnimatedBuilder(animation: _controller, builder: (context, child) => Container(
      margin: const EdgeInsets.only(bottom: 20), padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(22),
          border: Border.all(color: CampusPulse.color.withValues(alpha: .15 + _controller.value * .2))),
      child: Row(children: [
        const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
        const SizedBox(width: 12),
        Expanded(child: Text(widget.searching ? '深读官网资料，正在为你整理…' : '正在查找相关资料…',
            style: const TextStyle(fontSize: 12))),
      ]),
    )),
  );
}

class CampusPulse { static const color = Color(0xFF257E67); }
