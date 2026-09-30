import { Injectable } from '@nestjs/common';
import { ThrottlerGuard } from '@nestjs/throttler';

// Behind Cloudflare + nginx every request shares the proxy IP, so key on the real client IP.
@Injectable()
export class LoginThrottlerGuard extends ThrottlerGuard {
  protected async getTracker(req: Record<string, any>): Promise<string> {
    const cf = req.headers?.['cf-connecting-ip'];
    const forwarded = req.headers?.['x-forwarded-for'];
    return (
      (typeof cf === 'string' && cf) ||
      (typeof forwarded === 'string' && forwarded.split(',')[0].trim()) ||
      req.ip
    );
  }
}
