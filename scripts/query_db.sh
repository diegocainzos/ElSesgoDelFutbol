#!/bin/bash
# Script para explorar la DB de forma rápida

cd "$(dirname "$0")"

sqlite3 -column -header data/articles.db << 'SQL'
.width 12 50 12

-- Estadísticas generales
SELECT 
    'Total artículos' as metric,
    COUNT(*) as value
FROM articles

UNION ALL

SELECT 
    'Con sentimiento',
    COUNT(*)
FROM articles
WHERE sentiment_label IS NOT NULL

UNION ALL

SELECT 
    'Sin sentimiento',
    COUNT(*)
FROM articles
WHERE sentiment_label IS NULL;

-- Top 5 jugadores con más artículos
SELECT '' as '', '' as '', '' as '';
SELECT 'TOP PLAYERS' as '', '' as '', '' as '';
SELECT '============' as '', '' as '', '' as '';

SELECT 
    player,
    COUNT(*) as total,
    MAX(published_at) as ultimo
FROM articles 
GROUP BY player 
ORDER BY total DESC 
LIMIT 5;

SQL
