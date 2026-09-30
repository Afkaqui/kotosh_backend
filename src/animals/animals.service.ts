import { Injectable, NotFoundException, ConflictException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { CreateAnimalDto } from './dto/create-animal.dto';
import { UpdateAnimalDto } from './dto/update-animal.dto';
import { CreateWeightRecordDto } from './dto/create-weight-record.dto';
import { PaginationDto } from '../common/dto/pagination.dto';
import { Prisma } from '@prisma/client';

@Injectable()
export class AnimalsService {
  constructor(private prisma: PrismaService) {}

  async create(dto: CreateAnimalDto) {
    const { weight, birthDate, ...rest } = dto;
    try {
      return await this.prisma.animal.create({
        data: {
          ...rest,
          birthDate: birthDate ? new Date(birthDate) : null,
          weight: weight ?? null,
          weightRecords: weight ? { create: { weight, notes: 'Peso inicial' } } : undefined,
        },
      });
    } catch (error) {
      this.rethrowDuplicate(error, dto.tag);
    }
  }

  async findAll(pagination: PaginationDto) {
    const [animals, total] = await Promise.all([
      this.prisma.animal.findMany({
        skip: pagination.skip,
        take: pagination.take,
        orderBy: { tag: 'asc' },
      }),
      this.prisma.animal.count(),
    ]);
    return { data: animals, total };
  }

  async findOne(id: string) {
    const animal = await this.prisma.animal.findUnique({
      where: { id },
      include: { weightRecords: { orderBy: { date: 'asc' } } },
    });
    if (!animal) throw new NotFoundException('Animal no encontrado');
    return animal;
  }

  async update(id: string, dto: UpdateAnimalDto) {
    await this.ensureExists(id);
    // Weight changes go through weight records so the history stays consistent.
    const { weight: _ignored, birthDate, ...rest } = dto;
    try {
      return await this.prisma.animal.update({
        where: { id },
        data: {
          ...rest,
          birthDate: birthDate ? new Date(birthDate) : undefined,
        },
      });
    } catch (error) {
      this.rethrowDuplicate(error, dto.tag);
    }
  }

  async remove(id: string) {
    await this.ensureExists(id);
    await this.prisma.animal.delete({ where: { id } });
    return { deleted: true };
  }

  async addWeightRecord(animalId: string, dto: CreateWeightRecordDto) {
    await this.ensureExists(animalId);
    const record = await this.prisma.weightRecord.create({
      data: {
        animalId,
        weight: dto.weight,
        date: dto.date ? new Date(dto.date) : new Date(),
        notes: dto.notes,
      },
    });
    await this.syncCurrentWeight(animalId);
    return record;
  }

  async removeWeightRecord(animalId: string, recordId: string) {
    const record = await this.prisma.weightRecord.findFirst({ where: { id: recordId, animalId } });
    if (!record) throw new NotFoundException('Registro de peso no encontrado');
    await this.prisma.weightRecord.delete({ where: { id: recordId } });
    await this.syncCurrentWeight(animalId);
    return { deleted: true };
  }

  async getWeightHistory(animalId: string) {
    await this.ensureExists(animalId);
    return this.prisma.weightRecord.findMany({
      where: { animalId },
      orderBy: { date: 'asc' },
    });
  }

  async getBehaviorHistory(animalId: string) {
    await this.ensureExists(animalId);
    const detections = await this.prisma.animalDetection.findMany({
      where: { animalId },
      include: {
        analysis: {
          select: {
            id: true,
            completedAt: true,
            startedAt: true,
            video: { select: { originalName: true } },
          },
        },
      },
    });

    return detections
      .map((d) => {
        const total = d.totalSeconds || 0;
        const pct = (v: number) => (total > 0 ? Math.round((v / total) * 1000) / 10 : 0);
        return {
          detectionId: d.id,
          analysisId: d.analysis.id,
          date: d.analysis.completedAt ?? d.analysis.startedAt,
          videoName: d.analysis.video.originalName,
          trackId: d.trackId,
          eatingSeconds: d.eatingSeconds,
          restingSeconds: d.restingSeconds,
          movingSeconds: d.movingSeconds,
          totalSeconds: total,
          eatingPct: pct(d.eatingSeconds),
          restingPct: pct(d.restingSeconds),
          movingPct: pct(d.movingSeconds),
        };
      })
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }

  async getDashboardStats() {
    const [totalAnimals, activeAnimals, avgWeight, byStatus, lastWeighing] = await Promise.all([
      this.prisma.animal.count(),
      this.prisma.animal.count({ where: { status: 'activo' } }),
      this.prisma.animal.aggregate({
        _avg: { weight: true },
        where: { weight: { not: null }, status: 'activo' },
      }),
      this.prisma.animal.groupBy({ by: ['status'], _count: { _all: true } }),
      this.prisma.weightRecord.findFirst({ orderBy: { date: 'desc' }, select: { date: true } }),
    ]);
    return {
      totalAnimals,
      activeAnimals,
      inactiveAnimals: totalAnimals - activeAnimals,
      averageWeight: Math.round((avgWeight._avg.weight ?? 0) * 10) / 10,
      byStatus: byStatus.map((s) => ({ status: s.status ?? 'activo', count: s._count._all })),
      lastWeighingDate: lastWeighing?.date ?? null,
    };
  }

  private async ensureExists(id: string) {
    const exists = await this.prisma.animal.findUnique({ where: { id }, select: { id: true } });
    if (!exists) throw new NotFoundException('Animal no encontrado');
  }

  private async syncCurrentWeight(animalId: string) {
    const latest = await this.prisma.weightRecord.findFirst({
      where: { animalId },
      orderBy: { date: 'desc' },
    });
    await this.prisma.animal.update({
      where: { id: animalId },
      data: { weight: latest?.weight ?? null },
    });
  }

  private rethrowDuplicate(error: unknown, tag?: string): never {
    if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === 'P2002') {
      throw new ConflictException(`Ya existe un animal con el arete "${tag}"`);
    }
    throw error;
  }
}
