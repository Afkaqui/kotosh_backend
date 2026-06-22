import { IsString, IsOptional, IsDateString } from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

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
}
