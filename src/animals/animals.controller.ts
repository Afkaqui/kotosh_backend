import { Controller, Get, Post, Patch, Delete, Param, Query, Body, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { Role } from '@prisma/client';
import { AnimalsService } from './animals.service';
import { CreateAnimalDto } from './dto/create-animal.dto';
import { UpdateAnimalDto } from './dto/update-animal.dto';
import { CreateWeightRecordDto } from './dto/create-weight-record.dto';
import { PaginationDto } from '../common/dto/pagination.dto';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { Roles, RolesGuard } from '../auth/guards/roles.guard';

@ApiTags('Animals')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard, RolesGuard)
@Controller('animals')
export class AnimalsController {
  constructor(private readonly animalsService: AnimalsService) {}

  @Post()
  @Roles(Role.ADMIN, Role.ENCARGADO)
  @ApiOperation({ summary: 'Registrar animal (admin/encargado)' })
  create(@Body() dto: CreateAnimalDto) {
    return this.animalsService.create(dto);
  }

  @Get('stats')
  @ApiOperation({ summary: 'Estadísticas del hato' })
  getStats() {
    return this.animalsService.getDashboardStats();
  }

  @Get()
  @ApiOperation({ summary: 'Listar animales' })
  findAll(@Query() pagination: PaginationDto) {
    return this.animalsService.findAll(pagination);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Ficha del animal con historial de peso' })
  findOne(@Param('id') id: string) {
    return this.animalsService.findOne(id);
  }

  @Patch(':id')
  @Roles(Role.ADMIN, Role.ENCARGADO)
  @ApiOperation({ summary: 'Actualizar animal (admin/encargado)' })
  update(@Param('id') id: string, @Body() dto: UpdateAnimalDto) {
    return this.animalsService.update(id, dto);
  }

  @Delete(':id')
  @Roles(Role.ADMIN, Role.ENCARGADO)
  @ApiOperation({ summary: 'Eliminar animal (admin/encargado)' })
  remove(@Param('id') id: string) {
    return this.animalsService.remove(id);
  }

  @Post(':id/weight')
  @ApiOperation({ summary: 'Registrar pesaje' })
  addWeight(@Param('id') id: string, @Body() dto: CreateWeightRecordDto) {
    return this.animalsService.addWeightRecord(id, dto);
  }

  @Get(':id/weight')
  @ApiOperation({ summary: 'Historial de peso' })
  getWeightHistory(@Param('id') id: string) {
    return this.animalsService.getWeightHistory(id);
  }

  @Delete(':id/weight/:recordId')
  @Roles(Role.ADMIN, Role.ENCARGADO)
  @ApiOperation({ summary: 'Eliminar registro de peso (admin/encargado)' })
  removeWeight(@Param('id') id: string, @Param('recordId') recordId: string) {
    return this.animalsService.removeWeightRecord(id, recordId);
  }

  @Get(':id/behavior')
  @ApiOperation({ summary: 'Historial de comportamiento (detecciones asignadas)' })
  getBehavior(@Param('id') id: string) {
    return this.animalsService.getBehaviorHistory(id);
  }
}
