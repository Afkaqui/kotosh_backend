import { Controller, Get } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';

@ApiTags('Health')
@Controller()
export class AppController {
  @Get()
  @ApiOperation({ summary: 'Health check' })
  getHealth() {
    return { status: 'ok', timestamp: new Date().toISOString() };
  }
}
