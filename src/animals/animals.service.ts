import { Injectable, NotFoundException, ConflictException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { CreateAnimalDto } from './dto/create-animal.dto';
import { UpdateAnimalDto } from './dto/update-animal.dto';
import { PaginationDto } from '../common/dto/pagination.dto';
import { Prisma } from '@prisma/client';

@Injectable()
export class AnimalsService {
  constructor(private prisma: PrismaService) {}

  async create(dto: CreateAnimalDto) {
    try {
      return await this.prisma.animal.create({
        data: {
          ...dto,
          birthDate: dto.birthDate ? new Date(dto.birthDate) : null,
        },
      });
    } catch (error) {
      if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === 'P2002') {
        throw new ConflictException(`Ya existe un animal con tag "${dto.tag}"`);
      }
      throw error;
    }
  }

  async findAll(pagination: PaginationDto) {
    const [animals, total] = await Promise.all([
      this.prisma.animal.findMany({
        skip: pagination.skip,
        take: pagination.take,
        orderBy: { createdAt: 'desc' },
      }),
      this.prisma.animal.count(),
    ]);
    return { data: animals, total };
  }

  async findOne(id: string) {
    const animal = await this.prisma.animal.findUnique({ where: { id } });
    if (!animal) throw new NotFoundException('Animal no encontrado');
    return animal;
  }

  async update(id: string, dto: UpdateAnimalDto) {
    await this.findOne(id);
    try {
      return await this.prisma.animal.update({
        where: { id },
        data: {
          ...dto,
          birthDate: dto.birthDate ? new Date(dto.birthDate) : undefined,
        },
      });
    } catch (error) {
      if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === 'P2002') {
        throw new ConflictException(`Ya existe un animal con tag "${dto.tag}"`);
      }
      throw error;
    }
  }

  async remove(id: string) {
    await this.findOne(id);
    await this.prisma.animal.delete({ where: { id } });
    return { deleted: true };
  }
}
