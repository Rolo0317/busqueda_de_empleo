"""PyMySQL en lugar de mysqlclient: es Python puro y evita la compilacion nativa
que en Windows suele ser el motivo de que el backend no arranque."""
import pymysql

pymysql.install_as_MySQLdb()
