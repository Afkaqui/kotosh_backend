import { IsString, IsOptional, IsDateString, IsIn, IsNumber, Min, Max } from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export const ANIMAL_STATUSES = ['activo', 'en_tratamiento', 'vendido', 'baja'] as const;

export class CreateAnimalDto {
  @ApiProperty({ example: 'B-001' })
  @IsString()
  tag: string;

  @ApiPropertyOptional({ example: 'Luna' })
  @IsOptional()
  @IsString()
  name?: string;

  @ApiPropertyOptional({ example: 'Brown Swiss' })
  @IsOptional()
  @IsString()
  breed?: string;

  @ApiPropertyOptional({ example: 'F' })
  @IsOptional()
  @IsString()
  sex?: string;

  @ApiPropertyOptional({ example: '2022-03-15' })
  @IsOptional()
  @IsDateString()
  birthDate?: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  notes?: string;

  @ApiPropertyOptional({ enum: ANIMAL_STATUSES, default: 'activo' })
  @IsOptional()
  @IsIn(ANIMAL_STATUSES)
  status?: string;

  @ApiPropertyOptional({ example: 420, description: 'Peso inicial en kg; crea el primer registro de pesaje' })
  @IsOptional()
  @IsNumber()
  @Min(1)
  @Max(2000)
  weight?: number;
}
