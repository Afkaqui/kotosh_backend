export default () => ({
  port: parseInt(process.env.PORT ?? '3000', 10),
  database: {
    url: process.env.DATABASE_URL ?? '',
  },
  jwt: {
    // No fallback in production: the app refuses to start without JWT_SECRET.
    secret:
      process.env.JWT_SECRET ??
      (process.env.NODE_ENV === 'production' ? undefined : 'kotosh-jwt-secret-dev-only'),
    expiresIn: process.env.JWT_EXPIRES_IN ?? '7d',
  },
  ml: {
    serviceUrl: process.env.ML_SERVICE_URL ?? 'http://localhost:8000',
  },
  upload: {
    dir: process.env.UPLOAD_DIR ?? './uploads',
    maxFileSize: parseInt(process.env.MAX_FILE_SIZE ?? '524288000', 10),
  },
});
