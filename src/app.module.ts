import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { AppController } from './app.controller';
import { PrismaModule } from './prisma/prisma.module';
import { VideosModule } from './videos/videos.module';
import { AnalysisModule } from './analysis/analysis.module';
import { AnimalsModule } from './animals/animals.module';
import { MetricsModule } from './metrics/metrics.module';
import { AuthModule } from './auth/auth.module';
import configuration from './config/configuration';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true, load: [configuration] }),
    PrismaModule,
    VideosModule,
    AnalysisModule,
    AnimalsModule,
    MetricsModule,
    AuthModule,
  ],
  controllers: [AppController],
})
export class AppModule {}
