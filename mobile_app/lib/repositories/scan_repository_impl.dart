import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart';

import '../config/app_config.dart';
import '../models/disease_prediction.dart';
import '../services/http_client.dart';
import '../utils/error_mapper.dart';
import 'scan_repository.dart';

class ScanRepositoryImpl implements ScanRepository {
  const ScanRepositoryImpl({required this._client});

  final HttpClient _client;

  @override
  Future<DiseasePrediction> scan(String filePath) async {
    final file = File(filePath);
    final ext = filePath.split('.').last.toLowerCase();
    final mediaType = (ext == 'png')
        ? MediaType('image', 'png')
        : (ext == 'webp' ? MediaType('image', 'webp') : MediaType('image', 'jpeg'));
    final multipartFile = await MultipartFile.fromPath(
      'image',
      file.path,
      contentType: mediaType,
    );
    final streamed = await _client.multipartPost(
      AppConfig.apiUri('/crop-health/scan'),
      fields: const <String, String>{},
      files: <MultipartFile>[multipartFile],
    );
    final response = await Response.fromStream(streamed);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    return DiseasePrediction.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  @override
  Future<List<DiseasePrediction>> getHistory() async {
    final response = await _client.get(AppConfig.apiUri('/crop-health/history'));
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = (body['data'] as List<dynamic>?) ?? <dynamic>[];
    return data
        .whereType<Map<String, dynamic>>()
        .map(DiseasePrediction.fromJson)
        .toList(growable: false);
  }
}
