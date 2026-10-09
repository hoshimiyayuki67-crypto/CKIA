import 'reply_service.dart';
part 'school_catalogue.g.dart';

class School {
  const School(this.id, this.name, this.domain, {this.province = '', this.city = '',
      this.pinyin = '', this.initials = '', this.code = ''});
  final String id, name, domain;
  final String province, city, pinyin, initials, code;
  bool matches(String query) {
    final q = query.toLowerCase().replaceAll(' ', '');
    return [name, city, province, pinyin, initials, code]
        .any((value) => value.toLowerCase().replaceAll(' ', '').contains(q));
  }
  Json toJson() => {'id': id, 'name': name, 'domain': domain,
      'province': province, 'city': city, 'pinyin': pinyin, 'initials': initials, 'code': code};
  factory School.fromJson(Json json) => School(json['id'] as String,
      json['name'] as String, json['domain'] as String? ?? '',
      province: json['province'] as String? ?? '', city: json['city'] as String? ?? '',
      pinyin: json['pinyin'] as String? ?? '', initials: json['initials'] as String? ?? '',
      code: json['code'] as String? ?? '');
}

Future<List<School>> loadSchoolCatalogue() async {
  return schoolCatalogue;
}

const schools = [
  School('imuchuangye', '内蒙古大学创业学院', 'imuchuangye.cn'),
  School('imu', '内蒙古大学', 'imu.edu.cn'),
  School('pku', '北京大学', 'pku.edu.cn'),
  School('tsinghua', '清华大学', 'tsinghua.edu.cn'),
];
