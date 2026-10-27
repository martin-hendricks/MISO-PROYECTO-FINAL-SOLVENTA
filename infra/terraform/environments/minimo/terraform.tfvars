# El deploy completo de todo el backend (8 servicios del Grupo B
# desplegando a la vez, 2-4 réplicas cada uno) satura el límite original (6)
# del Node Group B durante el rolling update -- varios jobs "Verificar
# rollout" fallan por timeout de 120s con pods en Pending ("1 max node group
# size reached"). Queda en 10 de forma permanente para que levantar el
# ambiente desde cero (o un deploy completo) no vuelva a topar con esto.
node_group_b_max_size = 10
