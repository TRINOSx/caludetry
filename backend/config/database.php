<?php
/**
 * Database Configuration
 * Supports PostgreSQL (TimescaleDB) and MySQL
 */

class Database {
    private static $instance = null;

    // Configuration - modify for your environment
    private static $config = [
        'driver' => 'pgsql', // 'pgsql' for TimescaleDB, 'mysql' for MySQL
        'host' => 'localhost',
        'port' => '5432',    // 5432 for PostgreSQL, 3306 for MySQL
        'dbname' => 'voc_field',
        'username' => 'voc_user',
        'password' => 'voc_password',
        'charset' => 'utf8',
    ];

    /**
     * Get database connection (singleton)
     */
    public static function connect() {
        if (self::$instance === null) {
            try {
                $driver = self::$config['driver'];
                $host = self::$config['host'];
                $port = self::$config['port'];
                $dbname = self::$config['dbname'];
                $charset = self::$config['charset'];

                if ($driver === 'pgsql') {
                    $dsn = "pgsql:host=$host;port=$port;dbname=$dbname";
                } else {
                    $dsn = "mysql:host=$host;port=$port;dbname=$dbname;charset=$charset";
                }

                self::$instance = new PDO(
                    $dsn,
                    self::$config['username'],
                    self::$config['password'],
                    [
                        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                        PDO::ATTR_EMULATE_PREPARES => false,
                    ]
                );
            } catch (PDOException $e) {
                throw new Exception("Database connection failed: " . $e->getMessage());
            }
        }

        return self::$instance;
    }

    /**
     * Override config (for testing or different environments)
     */
    public static function setConfig($config) {
        self::$config = array_merge(self::$config, $config);
        self::$instance = null; // Reset connection
    }
}
