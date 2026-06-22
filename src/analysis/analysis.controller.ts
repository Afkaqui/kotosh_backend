import { Controller, Get, Post, Param, Query } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { AnalysisService } from './analysis.service';
import { PaginationDto } from '../common/dto/pagination.dto';

@ApiTags('Analysis')
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
}
