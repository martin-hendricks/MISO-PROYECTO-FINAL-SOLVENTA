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
# margen para un rollout sin agotar la cuota. Grupo B corre los otros 7
# servicios -- 5 de techo (10 vCPU) deja 1 nodo de colchón bajo las 16 vCPU
# totales (14 vCPU en el peor caso A+B), porque CloudWatch puede seguir
# contando una instancia en terminación un rato (visto: 18 vCPU reportadas
# con 9 nodos corriendo, cuando en teoría eran 16).
node_group_a_max_size = 2
node_group_b_max_size = 5
