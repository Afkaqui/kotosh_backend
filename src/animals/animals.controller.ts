import { Controller, Get, Post, Patch, Delete, Param, Query, Body } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { AnimalsService } from './animals.service';
import { CreateAnimalDto } from './dto/create-animal.dto';
import { UpdateAnimalDto } from './dto/update-animal.dto';
import { PaginationDto } from '../common/dto/pagination.dto';

@ApiTags('Animals')
@Controller('animals')
export class AnimalsController {
  constructor(private readonly animalsService: AnimalsService) {}

  @Post()
  @ApiOperation({ summary: 'Registrar animal' })
  create(@Body() dto: CreateAnimalDto) {
    return this.animalsService.create(dto);
  }

  @Get()
  @ApiOperation({ summary: 'Listar animales' })
  findAll(@Query() pagination: PaginationDto) {
    return this.animalsService.findAll(pagination);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Obtener animal por ID' })
  findOne(@Param('id') id: string) {
    return this.animalsService.findOne(id);
  }

  @Patch(':id')
  @ApiOperation({ summary: 'Actualizar animal' })
  update(@Param('id') id: string, @Body() dto: UpdateAnimalDto) {
    return this.animalsService.update(id, dto);
  }

  @Delete(':id')
  @ApiOperation({ summary: 'Eliminar animal' })
  remove(@Param('id') id: string) {
    return this.animalsService.remove(id);
  }
}
