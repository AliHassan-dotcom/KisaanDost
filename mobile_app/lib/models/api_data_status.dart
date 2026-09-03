enum ApiDataStatus {
  live,
  historical,
  mock,
  unavailable,
  error;

  static ApiDataStatus fromJson(String? value) {
    switch (value?.toLowerCase()) {
      case 'live':
      case 'official_amis':
      case 'fresh_live':
      case 'cached_live':
        return ApiDataStatus.live;
      case 'historical':
      case 'stale_official_record':
      case 'stale_live_cache':
      case 'stale_fallback':
        return ApiDataStatus.historical;
      case 'mock':
        return ApiDataStatus.mock;
      case 'unavailable':
      case 'source_unavailable':
      case null:
        return ApiDataStatus.unavailable;
      default:
        return ApiDataStatus.error;
    }
  }

  String toJson() => name;
}
