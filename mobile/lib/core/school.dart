import 'reply_service.dart';

class School {
  const School(this.id, this.name, this.domain);
  final String id, name, domain;
  Json toJson() => {'id': id, 'name': name, 'domain': domain};
  factory School.fromJson(Json json) => School(json['id'] as String,
      json['name'] as String, json['domain'] as String);
}

const schools = [
  School('imuchuangye', '内蒙古大学创业学院', 'imuchuangye.cn'),
  School('imu', '内蒙古大学', 'imu.edu.cn'),
  School('pku', '北京大学', 'pku.edu.cn'),
  School('tsinghua', '清华大学', 'tsinghua.edu.cn'),
];
