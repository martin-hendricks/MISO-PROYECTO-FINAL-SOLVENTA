# Presupuesto real de la cuenta: la cuota de EC2 "Running On-Demand
# Standard (A,C,D,H,I,M,R,T,Z) instances" es 16 vCPU (confirmado con
# `aws service-quotas get-service-quota --service-code ec2 --quota-code
# L-1216C47A`). Con t3.small (2 vCPU) en ambos Node Groups, eso es un techo
# de 8 nodos TOTALES entre Grupo A + Grupo B combinados -- no 6-10 en cada
# uno por separado. Pasarse de la cuota real no es un error de
# configuración de Kubernetes/Helm: el Cluster Autoscaler sube
# desired_size igual, pero el ASG falla el lanzamiento de la instancia con
# "VcpuLimitExceeded" (visto en `aws autoscaling describe-scaling-activities`)
# y el pod nuevo queda en Pending indefinidamente.
#
# Reparto: Grupo A corre solo ms-cotizacion + ms-perfilamiento, ambos ya
# bajados a replicas:1/400Mi -- con 1 nodo sobra holgado; 2 de techo da
# margen para un rollout sin agotar la cuota.
#
# Grupo B corre los otros 8 servicios (bff-web, api-socios, bff-movil,
# ms-pagos, ms-polizas, ms-suscripcion, ms-identidad, ms-siniestros). Con
# 5 nodos (visto en el cluster real, 2026-10-30, 17 réplicas deseadas en
# reposo en ese momento) dejaba ~76% de memoria reservada en promedio,
# pero el bin-packing real del scheduler no distribuye parejo -- se vieron
# nodos al 91% junto a uno al 63%, suficiente para dejar pods en Pending
# indefinido (FailedScheduling "Insufficient memory") aun con el sizing de
# cada pod ya correcto.
#
# Dos ajustes juntos: bff-web bajado de 3 a 1 réplica (ver
# infra/k8s/values/bff-web.yaml -- era el de mayor footprint individual,
# 384Mi, entre los que seguían en 3) Y node_group_b_max_size subido a 6
# (12 vCPU), para dar margen real de bin-packing además de bajar la
# demanda total. Total máximo entre ambos grupos: 2 + 6 = 8 nodos = 16
# vCPU, exactamente en el límite de cuota, sin colchón adicional -- si
# vuelve a quedarse corto, la palanca es bajar replicas/minReplicas de
# algún otro servicio del Grupo B antes que seguir subiendo
# node_group_b_max_size (ya en el límite de cuota real).
node_group_a_max_size = 2
node_group_b_max_size = 6
