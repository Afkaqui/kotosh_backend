import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class MetricsService {
  constructor(private prisma: PrismaService) {}

  async getDashboard() {
    const [totalVideos, totalAnalyses, totalAnimalsDetected, recentAnalyses] =
      await Promise.all([
        this.prisma.video.count(),
        this.prisma.analysis.count({ where: { status: 'COMPLETED' } }),
        this.prisma.animalDetection.count(),
        this.prisma.analysis.findMany({
          where: { status: 'COMPLETED' },
          orderBy: { completedAt: 'desc' },
          take: 5,
          include: {
            video: { select: { originalName: true } },
            _count: { select: { detections: true } },
          },
        }),
      ]);

    const allDetections = await this.prisma.animalDetection.findMany({
      select: { eatingSeconds: true, restingSeconds: true, movingSeconds: true, totalSeconds: true },
    });

    let avgBehavior = { eating: 0, resting: 0, moving: 0 };
    if (allDetections.length > 0) {
      const totals = allDetections.reduce(
        (acc, d) => ({
          eating: acc.eating + d.eatingSeconds,
          resting: acc.resting + d.restingSeconds,
          moving: acc.moving + d.movingSeconds,
          total: acc.total + d.totalSeconds,
        }),
        { eating: 0, resting: 0, moving: 0, total: 0 },
      );

      if (totals.total > 0) {
        avgBehavior = {
          eating: Math.round((totals.eating / totals.total) * 1000) / 10,
          resting: Math.round((totals.resting / totals.total) * 1000) / 10,
          moving: Math.round((totals.moving / totals.total) * 1000) / 10,
        };
      }
    }

    return {
      totalVideos,
      totalAnalyses,
      totalAnimalsDetected,
      avgBehavior,
      recentAnalyses,
    };
  }

  async getBehaviorDistribution() {
    const analyses = await this.prisma.analysis.findMany({
      where: { status: 'COMPLETED' },
      orderBy: { completedAt: 'desc' },
      take: 20,
      include: {
        video: { select: { originalName: true } },
        detections: {
          select: {
            trackId: true,
            eatingSeconds: true,
            restingSeconds: true,
            movingSeconds: true,
            totalSeconds: true,
          },
        },
      },
    });

    return analyses.map((a) => ({
      id: a.id,
      videoName: a.video.originalName,
      completedAt: a.completedAt,
      animals: a.detections.map((d) => ({
        trackId: d.trackId,
        eating: d.totalSeconds > 0 ? Math.round((d.eatingSeconds / d.totalSeconds) * 100) : 0,
        resting: d.totalSeconds > 0 ? Math.round((d.restingSeconds / d.totalSeconds) * 100) : 0,
        moving: d.totalSeconds > 0 ? Math.round((d.movingSeconds / d.totalSeconds) * 100) : 0,
      })),
    }));
  }
}
