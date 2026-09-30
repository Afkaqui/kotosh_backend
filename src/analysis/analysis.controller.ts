import { Controller, Get, Post, Patch, Param, Query, Body, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { IsOptional, IsString } from 'class-validator';
import { AnalysisService } from './analysis.service';
import { PaginationDto } from '../common/dto/pagination.dto';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';

class AssignDetectionDto {
  @IsOptional()
  @IsString()
  animalId?: string | null;
}

@ApiTags('Analysis')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller()
export class AnalysisController {
  constructor(private readonly analysisService: AnalysisService) {}

  @Post('videos/:id/analyze')
  @ApiOperation({ summary: 'Disparar análisis ML de un video' })
  triggerAnalysis(@Param('id') id: string) {
    return this.analysisService.triggerAnalysis(id);
  }

  @Get('analyses')
  @ApiOperation({ summary: 'Listar análisis' })
  findAll(@Query() pagination: PaginationDto) {
    return this.analysisService.findAll(pagination);
  }

  @Get('analyses/:id')
  @ApiOperation({ summary: 'Obtener análisis por ID' })
  findOne(@Param('id') id: string) {
    return this.analysisService.findOne(id);
  }

  @Patch('detections/:id/animal')
  @ApiOperation({ summary: 'Asignar una detección (track) a un animal registrado' })
  assign(@Param('id') id: string, @Body() dto: AssignDetectionDto) {
    return this.analysisService.assignDetection(id, dto.animalId || null);
  }
}
