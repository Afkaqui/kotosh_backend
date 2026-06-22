import {
  Controller,
  Get,
  Post,
  Delete,
  Param,
  Query,
  UploadedFile,
  UseInterceptors,
  ParseFilePipe,
  MaxFileSizeValidator,
  FileTypeValidator,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { diskStorage } from 'multer';
import { extname } from 'path';
import { v4 as uuidv4 } from 'uuid';
import { ApiTags, ApiOperation, ApiConsumes, ApiBody } from '@nestjs/swagger';
import { VideosService } from './videos.service';
import { PaginationDto } from '../common/dto/pagination.dto';
import { UploadVideoDto } from './dto/upload-video.dto';

@ApiTags('Videos')
@Controller('videos')
export class VideosController {
  constructor(private readonly videosService: VideosService) {}

  @Post('upload')
  @ApiOperation({ summary: 'Subir video' })
  @ApiConsumes('multipart/form-data')
  @ApiBody({ type: UploadVideoDto })
  @UseInterceptors(
    FileInterceptor('file', {
      storage: diskStorage({
        destination: './uploads',
        filename: (_req, file, cb) => {
          const uniqueName = `${uuidv4()}${extname(file.originalname)}`;
          cb(null, uniqueName);
        },
      }),
    }),
  )
  async upload(
    @UploadedFile(
      new ParseFilePipe({
        validators: [
          new MaxFileSizeValidator({ maxSize: 524288000 }),
          new FileTypeValidator({ fileType: /video\/(mp4|avi|quicktime|x-msvideo)/ }),
        ],
      }),
    )
    file: Express.Multer.File,
  ) {
    return this.videosService.create(file);
  }

  @Get()
  @ApiOperation({ summary: 'Listar videos' })
  findAll(@Query() pagination: PaginationDto) {
    return this.videosService.findAll(pagination);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Obtener video por ID' })
  findOne(@Param('id') id: string) {
    return this.videosService.findOne(id);
  }

  @Delete(':id')
  @ApiOperation({ summary: 'Eliminar video' })
  remove(@Param('id') id: string) {
    return this.videosService.remove(id);
  }
}
