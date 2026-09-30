import { Controller, Get, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { MetricsService } from './metrics.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';

@ApiTags('Metrics')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller('metrics')
export class MetricsController {
  constructor(private readonly metricsService: MetricsService) {}

  @Get('dashboard')
  @ApiOperation({ summary: 'Métricas del dashboard' })
  getDashboard() {
    return this.metricsService.getDashboard();
  }

  @Get('behavior-distribution')
  @ApiOperation({ summary: 'Distribución de comportamiento por análisis' })
  getBehaviorDistribution() {
    return this.metricsService.getBehaviorDistribution();
  }
}
