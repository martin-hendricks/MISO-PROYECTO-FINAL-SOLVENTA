# infra/k8s — manifiestos de Kubernetes para Solventa sobre EKS

## Frontera con Terraform

Según lo acordado en `infra/terraform/PLAN.md` (tabla "Frontera Terraform / Kubernetes"):

> Terraform llega hasta los add-ons del clúster (ALB Controller, Cluster Autoscaler, External Secrets, Metrics Server); los 14 componentes de aplicación (12 microservicios + 2 BFF, más `api-socios`, `analitica` y `notificaciones`) viven en manifiestos `k8s/`.

Razones de esta frontera:

- **Destructibilidad (HU-78).** `terraform destroy` debe dejar la cuenta de AWS limpia. Si los Deployments/HPA de los microservicios estuvieran en el state de Terraform, cada `apply`/`destroy` tocaría también el ciclo de vida de la aplicación, y un `plan` de infraestructura empezaría a mostrar diffs de cosas que cambian por CI/CD (tags de imagen, réplicas ajustadas por HPA), no por cambios de infraestructura.
- **Redespliegue de un microservicio no debe pasar por `terraform apply`.** Publicar una nueva versión de `ms-cotizacion` es una operación de `kubectl`/`helm` sobre el clúster ya existente, no una operación que reconcilie VPCs, RDS o Secrets Manager.
- **El autoescalado de aplicación (EC-ESC-01/02/03) se ajusta con un HPA de Kubernetes**, no con un `desired_size` de Terraform. Por eso los node groups de EKS (`grupo_a`, `grupo_b`) tienen `lifecycle { ignore_changes = [scaling_config[0].desired_size] }`: Terraform fija los límites (`min_size`/`max_size`) y dueño de la infraestructura; Cluster Autoscaler + HPA deciden cuántos nodos y pods hay en cada momento.

Esta carpeta (`infra/k8s/`) es justamente el lado "aplicación" de esa frontera. No se ejecuta `kubectl apply` ni `helm install` desde este repositorio como parte de esta tarea; solo se documentan y versionan los manifiestos.

## Estructura

```
infra/k8s/
├── README.md
├── charts/
│   └── microservicio/       # chart genérico de Helm (un chart, muchos values) — NO se toca aquí
├── values/                  # un values.yaml por componente, para el chart genérico
│   ├── ms-cotizacion.yaml        (Grupo A)
│   ├── ms-perfilamiento.yaml     (Grupo A)
│   ├── ms-suscripcion.yaml       (Grupo B)
│   ├── ms-polizas.yaml           (Grupo B)
│   ├── ms-siniestros.yaml        (Grupo B)
│   ├── ms-parametrico.yaml       (Grupo B)
│   ├── ms-consentimiento.yaml    (Grupo B)
│   ├── ms-identidad.yaml         (Grupo B)
│   ├── ms-pagos.yaml             (Grupo B)
│   ├── bff-web.yaml              (Grupo B)
│   ├── bff-movil.yaml            (Grupo B)
│   ├── api-socios.yaml           (Grupo B)
│   ├── analitica.yaml            (Grupo B)
│   └── notificaciones.yaml       (Grupo B)
└── platform/                 # manifiestos transversales, no específicos de un componente
    ├── namespace.yaml
    ├── clustersecretstore.yaml
    ├── ingress.yaml
    └── networkpolicies.yaml
```

## Orden de despliegue

1. `terraform apply` en `infra/terraform/environments/minimo` — crea VPC, EKS (control plane + node groups A/B), ECR, RDS, Redis, MSK, Secrets Manager, y los add-ons del clúster (ALB Controller, Cluster Autoscaler, External Secrets Operator, Metrics Server) vía `helm_release` dentro del propio módulo `eks_addons`.
2. `aws eks update-kubeconfig --name <cluster_name> --region us-east-1` — el comando exacto lo da el output `kubeconfig_command` de Terraform.
3. `kubectl apply -f infra/k8s/platform/namespace.yaml` — crea los namespaces `solventa` y `solventa-observability`.
4. `kubectl apply -f infra/k8s/platform/clustersecretstore.yaml` — habilita el puente entre External Secrets y AWS Secrets Manager. Debe ir antes que cualquier servicio, porque cada `ExternalSecret` de cada componente lo referencia por nombre (`solventa-secretstore`).
5. Publicar/etiquetar las imágenes en ECR (ver más abajo) y luego instalar cada componente con `helm install`/`helm upgrade` usando el chart genérico + el `values/<componente>.yaml` correspondiente.
6. `kubectl apply -f infra/k8s/platform/ingress.yaml` — expone `bff-web`, `bff-movil` y `api-socios` a través de un único ALB (requiere que el AWS Load Balancer Controller ya esté corriendo, paso 1).
7. `kubectl apply -f infra/k8s/platform/networkpolicies.yaml` — aplica el default-deny y las reglas de permiso explícitas. Se aplica al final a propósito: si se aplica antes de tener los pods con las labels correctas (`app.kubernetes.io/name`), el efecto es el mismo (deny hasta que existan los pods que matchean los selectors), pero conviene desplegarla después de validar que los servicios ya se ven entre sí, para no mezclar depuración de red con depuración de despliegue inicial.

## Cómo se conectan los outputs de Terraform con estos manifiestos

Ningún manifiesto de esta carpeta referencia el state de Terraform directamente (no hay `terraform_remote_state` ni plugins de sustitución automática): la conexión es manual/documental, a propósito, para no romper la frontera. Los puntos de unión son:

| Output de Terraform (`environments/minimo/outputs.tf`) | Dónde se usa en `k8s/` |
| --- | --- |
| `ecr_repository_urls["<componente>"]` | `imagen.repositorio` en cada `values/<componente>.yaml`. Hoy tiene el placeholder `<account>.dkr.ecr.us-east-1.amazonaws.com/solventa-minimo-<componente>`; hay que sustituir `<account>` por el account ID real (o generar los values con un template que lo inyecte en CI/CD). |
| `secret_arns` (y los nombres fijos `solventa-minimo-<recurso>-credentials`) | `externalSecrets.remoteSecrets[].nombreRemoto` en cada `values/<componente>.yaml`, y el `provider.aws.region` del `ClusterSecretStore` (`platform/clustersecretstore.yaml`). El ClusterSecretStore no necesita el ARN explícito: resuelve por nombre de secreto dentro de la región configurada. |
| `cluster_name`, `kubeconfig_command` | Paso 2 de despliegue, arriba. |
| `polizas_writer_endpoint` / `polizas_reader_endpoint` | `values/ms-polizas.yaml` → `variablesEntorno[DB_POLIZAS_WRITE_HOST]` / `[DB_POLIZAS_READ_HOST]`. |
| `siniestros_endpoint` | `values/ms-siniestros.yaml` → `variablesEntorno[DB_SINIESTROS_HOST]`. |
| `redis_primary_endpoint` | `values/ms-cotizacion.yaml` y `values/ms-perfilamiento.yaml` → `REDIS_CACHE_OF_HOST` / `REDIS_CACHE_OD_HOST`. |
| `msk_bootstrap_brokers_sasl_iam` | `values/ms-parametrico.yaml`, `values/ms-pagos.yaml`, `values/analitica.yaml`, `values/notificaciones.yaml` → `MSK_BOOTSTRAP_BROKERS`. |
| `evidencias_bucket_name` | `values/ms-siniestros.yaml` → `S3_EVIDENCIAS_BUCKET`. |
| Rol IRSA de `external-secrets` (módulo `eks_addons`) | `platform/clustersecretstore.yaml` → `spec.provider.aws.auth.jwt.serviceAccountRef` (apunta al ServiceAccount `external-secrets`/`external-secrets`, que Terraform ya anota con ese rol). |
| Rol IRSA de `aws-load-balancer-controller` (módulo `eks_addons`) | Implícito: es el controlador que interpreta `platform/ingress.yaml`. No hay nada que copiar a mano aquí. |

Todos esos puntos quedan marcados con `# TODO: reemplazar por <output> (output de Terraform)` en los archivos de `values/` para que sean fáciles de encontrar y automatizar (por ejemplo, con `envsubst`/`kustomize`/un job de CI que corra `terraform output -json` y parchee estos valores antes del `helm upgrade`).

## Instalar un servicio

```bash
helm upgrade --install ms-cotizacion infra/k8s/charts/microservicio \
  --namespace solventa \
  --values infra/k8s/values/ms-cotizacion.yaml
```

El mismo comando aplica a cualquier otro componente, cambiando el nombre del release y el archivo de `--values`. El chart genérico vive en `infra/k8s/charts/microservicio/` (fuera del alcance de esta tarea) y expone el esquema de values documentado en cada archivo de `values/`.

## Validación de sintaxis usada en esta tarea

No hay clúster disponible, así que no se corrió `kubectl apply` ni `helm install`. Se validó únicamente sintaxis YAML:

```bash
python3 -c "import yaml,sys; [list(yaml.safe_load_all(open(f))) for f in sys.argv[1:]]" infra/k8s/values/*.yaml infra/k8s/platform/*.yaml
```

## TODO pendientes

- **Roles IRSA — el rol ya existe, falta copiar su ARN.** Los crea `modules/irsa_aplicacion`, uno por componente, con política mínima y trust policy atada a su ServiceAccount:
  - `ms-siniestros`: escritura de evidencia en S3.
  - `ms-parametrico`: consumo de `TopicoTelemetria` (MSK, auth IAM).
  - `ms-pagos`: consumo de `ColaPagos` (MSK, auth IAM).
  - `analitica` y `notificaciones`: consumo de `BusEventos` (MSK, auth IAM).

  El ARN incluye el account id, así que solo se conoce después del `apply`. Cada uno de esos cinco `values/*.yaml` lleva el comando exacto para obtenerlo:

  ```bash
  cd ../terraform/environments/minimo
  terraform output -json irsa_role_arns | jq -r '."ms-siniestros"'
  ```

  Si el `roleArn` queda vacío, el pod arranca pero falla al llamar a AWS: el ServiceAccount no lleva la anotación y no hay credenciales que presentar.
- **Tags de imagen.** `imagen.tag` queda vacío en los 14 `values/*.yaml` con `# TODO: tag de imagen`. Se decide en el pipeline de CI/CD (por ejemplo, el SHA corto del commit o un semver), no aquí.
- **`<account>` en `imagen.repositorio`.** Placeholder literal en los 14 archivos; se resuelve con `ecr_repository_urls` (ver tabla arriba) o con el account ID real una vez se corra `terraform apply`.
- **Endpoints de datos con placeholder `*.solventa.internal`.** `DB_POLIZAS_WRITE_HOST`/`READ_HOST`, `DB_SINIESTROS_HOST`, `REDIS_CACHE_OF_HOST`/`OD_HOST`, `MSK_BOOTSTRAP_BROKERS`, `S3_EVIDENCIAS_BUCKET`: todos marcados con TODO y el output de Terraform exacto que los reemplaza.
- **Certificado ACM y HTTPS del Ingress.** `platform/ingress.yaml` hoy solo escucha HTTP/HTTPS sin certificado; falta `alb.ingress.kubernetes.io/certificate-arn` cuando exista un dominio y certificado definidos.
- **NetworkPolicy real vs. CNI.** Las políticas de `platform/networkpolicies.yaml` asumen que el VPC CNI tiene "Network Policy" habilitado (`ENABLE_NETWORK_POLICY=true` en el addon `vpc-cni`, o Calico). Hoy el módulo `eks` de Terraform no fija ese flag explícitamente; verificar antes de depender de estas políticas para aislar tráfico en producción.
- **Prometheus/Grafana.** El namespace `solventa-observability` se creó en `platform/namespace.yaml` para alojar ese stack, pero los manifiestos/chart de Prometheus/Grafana no son parte de esta tarea.
