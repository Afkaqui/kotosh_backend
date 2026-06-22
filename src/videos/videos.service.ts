import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { PaginationDto } from '../common/dto/pagination.dto';
import { unlinkSync, existsSync } from 'fs';

@Injectable()
export class VideosService {
  constructor(private prisma: PrismaService) {}

  async create(file: Express.Multer.File) {
    return this.prisma.video.create({
      data: {
        filename: file.filename,
        originalName: file.originalname,
        path: file.path.replace(/\\/g, '/'),
        mimeType: file.mimetype,
        size: file.size,
      },
    });
  }

  async findAll(pagination: PaginationDto) {
    const [videos, total] = await Promise.all([
      this.prisma.video.findMany({
        skip: pagination.skip,
        take: pagination.take,
        orderBy: { uploadedAt: 'desc' },
        include: {
          analyses: {
            orderBy: { startedAt: 'desc' },
            take: 1,
            select: { id: true, status: true, startedAt: true, completedAt: true, summary: true },
          },
        },
      }),
      this.prisma.video.count(),
    ]);
    return { data: videos, total };
  }

  async findOne(id: string) {
    const video = await this.prisma.video.findUnique({
      where: { id },
      include: {
        analyses: {
          orderBy: { startedAt: 'desc' },
          include: { detections: true },
        },
      },
    });
    if (!video) throw new NotFoundException('Video no encontrado');
    return video;
  }

  async remove(id: string) {
    const video = await this.prisma.video.findUnique({ where: { id } });
    if (!video) throw new NotFoundException('Video no encontrado');

    if (existsSync(video.path)) {
      unlinkSync(video.path);
    }

    await this.prisma.video.delete({ where: { id } });
    return { deleted: true };
  }
}
