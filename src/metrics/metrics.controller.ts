import { Controller, Get } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { MetricsService } from './metrics.service';

@ApiTags('Metrics')
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
