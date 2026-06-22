import { Injectable, NotFoundException, Logger } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { PrismaService } from '../prisma/prisma.service';
import { PaginationDto } from '../common/dto/pagination.dto';
import { MlAnalysisResponse } from './interfaces/ml-response.interface';
import { resolve } from 'path';
import { firstValueFrom } from 'rxjs';

@Injectable()
export class AnalysisService {
  private readonly logger = new Logger(AnalysisService.name);

  constructor(
    private prisma: PrismaService,
    private httpService: HttpService,
    private configService: ConfigService,
  ) {}

  async triggerAnalysis(videoId: string) {
    const video = await this.prisma.video.findUnique({ where: { id: videoId } });
    if (!video) throw new NotFoundException('Video no encontrado');

    const analysis = await this.prisma.analysis.create({
      data: { videoId, status: 'PROCESSING' },
    });

    await this.prisma.video.update({
      where: { id: videoId },
      data: { status: 'PROCESSING' },
    });

    this.processAnalysis(analysis.id, video.path).catch((err) => {
      this.logger.error(`Analysis ${analysis.id} failed: ${err.message}`);
    });

    return analysis;
  }

  private async processAnalysis(analysisId: string, videoPath: string) {
    const mlUrl = this.configService.get<string>('ml.serviceUrl');
    const absolutePath = resolve(videoPath).replace(/\\/g, '/');

    try {
      const { data: mlResult } = await firstValueFrom(
        this.httpService.post<MlAnalysisResponse>(
          `${mlUrl}/analyze-video`,
          { video_path: absolutePath },
          { timeout: 600000 },
        ),
      );

      const detectionData = mlResult.animals.map((animal) => ({
        trackId: animal.track_id,
        label: animal.label,
        confidence: animal.confidence,
        eatingSeconds: animal.eating_seconds,
        restingSeconds: animal.resting_seconds,
        movingSeconds: animal.moving_seconds,
        totalSeconds: animal.total_seconds,
        behaviorLog: animal.behavior_log as unknown as object,
      }));

      const totalAnimals = mlResult.animals.length;
      const avgEatingPct = totalAnimals > 0
        ? mlResult.animals.reduce((s, a) => s + (a.eating_seconds / a.total_seconds) * 100, 0) / totalAnimals
        : 0;
      const avgRestingPct = totalAnimals > 0
        ? mlResult.animals.reduce((s, a) => s + (a.resting_seconds / a.total_seconds) * 100, 0) / totalAnimals
        : 0;
      const avgMovingPct = totalAnimals > 0
        ? mlResult.animals.reduce((s, a) => s + (a.moving_seconds / a.total_seconds) * 100, 0) / totalAnimals
        : 0;

      await this.prisma.analysis.update({
        where: { id: analysisId },
        data: {
          status: 'COMPLETED',
          fps: mlResult.fps,
          totalFrames: mlResult.total_frames,
          processedFrames: mlResult.processed_frames,
          completedAt: new Date(),
          summary: {
            totalAnimals,
            avgEatingPct: Math.round(avgEatingPct * 10) / 10,
            avgRestingPct: Math.round(avgRestingPct * 10) / 10,
            avgMovingPct: Math.round(avgMovingPct * 10) / 10,
            totalDurationSeconds: mlResult.total_frames / (mlResult.fps || 1),
          },
          detections: { create: detectionData },
        },
      });

      const analysis = await this.prisma.analysis.findUnique({ where: { id: analysisId } });
      if (analysis) {
        await this.prisma.video.update({
          where: { id: analysis.videoId },
          data: { status: 'COMPLETED' },
        });
      }
    } catch (error) {
      await this.prisma.analysis.update({
        where: { id: analysisId },
        data: {
          status: 'ERROR',
          errorMessage: error instanceof Error ? error.message : 'Error al procesar video',
          completedAt: new Date(),
        },
      });

      const analysis = await this.prisma.analysis.findUnique({ where: { id: analysisId } });
      if (analysis) {
        await this.prisma.video.update({
          where: { id: analysis.videoId },
          data: { status: 'ERROR' },
        });
      }
    }
  }

  async findAll(pagination: PaginationDto) {
    const [analyses, total] = await Promise.all([
      this.prisma.analysis.findMany({
        skip: pagination.skip,
        take: pagination.take,
        orderBy: { startedAt: 'desc' },
        include: {
          video: { select: { id: true, originalName: true } },
          _count: { select: { detections: true } },
        },
      }),
      this.prisma.analysis.count(),
    ]);
    return { data: analyses, total };
  }

  async findOne(id: string) {
    const analysis = await this.prisma.analysis.findUnique({
      where: { id },
      include: {
        video: { select: { id: true, originalName: true, filename: true } },
        detections: { orderBy: { trackId: 'asc' } },
      },
    });
    if (!analysis) throw new NotFoundException('Análisis no encontrado');
    return analysis;
  }
}
