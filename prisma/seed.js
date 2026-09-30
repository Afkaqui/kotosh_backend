// Creates the first ADMIN account. Usage: ADMIN_PASSWORD='...' node prisma/seed.js
const { PrismaClient } = require('@prisma/client');
const bcrypt = require('bcrypt');

const prisma = new PrismaClient();

async function main() {
  const email = (process.env.ADMIN_EMAIL || 'admin@kotosh.com').toLowerCase();
  const password = process.env.ADMIN_PASSWORD;
  const name = process.env.ADMIN_NAME || 'Administrador Kotosh';

  if (!password || password.length < 8) {
    throw new Error('Define ADMIN_PASSWORD (mínimo 8 caracteres) antes de ejecutar el seed.');
  }

  const existing = await prisma.user.findUnique({ where: { email } });
  if (existing) {
    console.log(`El usuario ${email} ya existe; no se modificó.`);
    return;
  }

  await prisma.user.create({
    data: { email, name, role: 'ADMIN', password: await bcrypt.hash(password, 10) },
  });
  console.log(`Administrador creado: ${email}`);
}

main()
  .catch((e) => {
    console.error(e.message);
    process.exitCode = 1;
  })
  .finally(() => prisma.$disconnect());
