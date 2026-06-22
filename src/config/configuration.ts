export default () => ({
  port: parseInt(process.env.PORT ?? '3000', 10),
  database: {
    url: process.env.DATABASE_URL ?? '',
  },
  ml: {
    serviceUrl: process.env.ML_SERVICE_URL ?? 'http://localhost:8000',
  },
  upload: {
    dir: process.env.UPLOAD_DIR ?? './uploads',
    maxFileSize: parseInt(process.env.MAX_FILE_SIZE ?? '524288000', 10),
  },
});
