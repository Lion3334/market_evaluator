import { Pool } from 'pg';
import dotenv from 'dotenv';

dotenv.config({ path: '../.env' });

const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    max: 20,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000,
});

pool.on('error', (err) => {
    console.error('Unexpected error on idle client', err);
    process.exit(-1);
});

export async function query<T>(text: string, params?: unknown[]): Promise<T[]> {
    const start = Date.now();
    const result = await pool.query(text, params);
    const duration = Date.now() - start;

    if (process.env.NODE_ENV === 'development') {
        console.log('Executed query', { text: text.substring(0, 50), duration, rows: result.rowCount });
    }

    return result.rows as T[];
}

export async function getClient() {
    const client = await pool.connect();
    return client;
}

export default pool;
