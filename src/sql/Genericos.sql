-- SQLite
INSERT INTO SIMULACAO (id, id_opcao, data_inicio, data_termino, quantidade, cenario)
VALUES (1,1,'2025-04-15','2025-05-16',1000,'DH-CALL-AJUSTE-D1');

UPDATE SIMULACAO SET id_opcao = 16 WHERE id = 1;

select * from SIMULACAO;

DELETE * from SIMULACAO 