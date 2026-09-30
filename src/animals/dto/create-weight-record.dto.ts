import { IsNumber, IsOptional, IsString, IsDateString, Min, Max } from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class CreateWeightRecordDto {
  @ApiProperty({ example: 450.5 })
  @IsNumber()
  @Min(1)
  @Max(2000)
  weight: number;

  @ApiPropertyOptional({ example: '2025-06-15' })
  @IsOptional()
  @IsDateString()
  date?: string;

  @ApiPropertyOptional({ example: 'Peso post-destete' })
  @IsOptional()
  @IsString()
  notes?: string;
}
