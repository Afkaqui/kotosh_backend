import {
  Injectable,
  UnauthorizedException,
  ConflictException,
  NotFoundException,
  BadRequestException,
} from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { Prisma, Role, User } from '@prisma/client';
import * as bcrypt from 'bcrypt';
import { PrismaService } from '../prisma/prisma.service';
import { RegisterDto } from './dto/register.dto';
import { LoginDto } from './dto/login.dto';
import { ChangePasswordDto } from './dto/change-password.dto';

const publicUser = {
  id: true,
  email: true,
  name: true,
  role: true,
  isActive: true,
  createdAt: true,
} as const;

@Injectable()
export class AuthService {
  constructor(
    private prisma: PrismaService,
    private jwtService: JwtService,
  ) {}

  async register(dto: RegisterDto) {
    const hashedPassword = await bcrypt.hash(dto.password, 10);
    try {
      return await this.prisma.user.create({
        data: {
          email: dto.email.toLowerCase().trim(),
          password: hashedPassword,
          name: dto.name.trim(),
          role: dto.role ?? Role.OPERARIO,
        },
        select: publicUser,
      });
    } catch (error) {
      if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === 'P2002') {
        throw new ConflictException('El correo ya está registrado');
      }
      throw error;
    }
  }

  async login(dto: LoginDto) {
    const user = await this.prisma.user.findUnique({
      where: { email: dto.email.toLowerCase().trim() },
    });
    if (!user || !user.isActive || !(await bcrypt.compare(dto.password, user.password))) {
      throw new UnauthorizedException('Credenciales inválidas');
    }
    return this.buildResponse(user);
  }

  async getProfile(userId: string) {
    const user = await this.prisma.user.findUnique({ where: { id: userId }, select: publicUser });
    if (!user) throw new UnauthorizedException();
    return user;
  }

  async changePassword(userId: string, dto: ChangePasswordDto) {
    const user = await this.prisma.user.findUnique({ where: { id: userId } });
    if (!user || !(await bcrypt.compare(dto.currentPassword, user.password))) {
      throw new BadRequestException('La contraseña actual no es correcta');
    }
    await this.prisma.user.update({
      where: { id: userId },
      data: { password: await bcrypt.hash(dto.newPassword, 10) },
    });
    return { updated: true };
  }

  findAllUsers() {
    return this.prisma.user.findMany({ select: publicUser, orderBy: { createdAt: 'desc' } });
  }

  async updateUserRole(actorId: string, userId: string, role: string) {
    if (!Object.values(Role).includes(role as Role)) {
      throw new BadRequestException('Rol inválido');
    }
    if (actorId === userId) {
      throw new BadRequestException('No puedes cambiar tu propio rol');
    }
    await this.ensureUser(userId);
    return this.prisma.user.update({
      where: { id: userId },
      data: { role: role as Role },
      select: publicUser,
    });
  }

  async toggleUserActive(actorId: string, userId: string) {
    if (actorId === userId) {
      throw new BadRequestException('No puedes desactivar tu propia cuenta');
    }
    const user = await this.ensureUser(userId);
    return this.prisma.user.update({
      where: { id: userId },
      data: { isActive: !user.isActive },
      select: publicUser,
    });
  }

  private async ensureUser(userId: string) {
    const user = await this.prisma.user.findUnique({ where: { id: userId } });
    if (!user) throw new NotFoundException('Usuario no encontrado');
    return user;
  }

  private buildResponse(user: User) {
    const { password: _password, ...userData } = user;
    return {
      access_token: this.jwtService.sign({ sub: user.id, email: user.email, role: user.role }),
      user: userData,
    };
  }
}
