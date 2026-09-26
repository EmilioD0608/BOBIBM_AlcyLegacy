import type {
  Request,
  Response,
} from "express";

import { randomUUID } from "node:crypto";
import { pool } from "../config/database.js";

// ============================================================
// CREAR JOB
// ============================================================

export async function createJob(
  req: Request,
  res: Response
) {
  try {
    if (!req.user?.id) {
      return res.status(401).json({
        success: false,
        error: "Usuario no autenticado.",
      });
    }

    const {
      repositoryId,
      jobType = "GITHUB",
      userSpecifications = null,
    } = req.body ?? {};

    // ========================================================
    // VALIDACIONES
    // ========================================================

    if (
      typeof repositoryId !== "string" ||
      !repositoryId.trim()
    ) {
      return res.status(400).json({
        success: false,
        error: "repositoryId es obligatorio.",
      });
    }

    const allowedJobTypes = [
      "FILE",
      "FOLDER",
      "GITHUB",
      "DOCUMENTATION",
    ];

    if (
      typeof jobType !== "string" ||
      !allowedJobTypes.includes(jobType)
    ) {
      return res.status(400).json({
        success: false,
        error: "El tipo de trabajo no es válido.",
      });
    }

    // ========================================================
    // VERIFICAR QUE EL REPOSITORIO PERTENECE AL USUARIO
    // ========================================================

    const repositoryResult =
      await pool.query<{
        id: string;
        full_name: string;
      }>(
        `
          SELECT
            id,
            full_name
          FROM repositories
          WHERE id = $1
            AND user_id = $2
          LIMIT 1
        `,
        [
          repositoryId,
          req.user.id,
        ]
      );

    const repository =
      repositoryResult.rows[0];

    if (!repository) {
      return res.status(404).json({
        success: false,
        error:
          "El repositorio no existe o no pertenece al usuario.",
      });
    }

    // ========================================================
    // CREAR JOB
    // ========================================================

    const jobId = randomUUID();

    const jobResult =
      await pool.query(
        `
          INSERT INTO jobs (
            id,
            user_id,
            repository_id,
            job_type,
            status,
            progress_percent,
            user_specifications
          )
          VALUES (
            $1,
            $2,
            $3,
            $4,
            'QUEUED',
            0,
            $5::jsonb
          )

          RETURNING
            id,
            user_id,
            repository_id,
            job_type,
            status,
            progress_percent,
            overall_risk_score,
            overall_risk_level,
            user_specifications,
            error_message,
            created_at,
            completed_at
        `,
        [
          jobId,
          req.user.id,
          repositoryId,
          jobType,
          userSpecifications === null
            ? null
            : JSON.stringify(
                userSpecifications
              ),
        ]
      );

    const job =
      jobResult.rows[0];

    // ========================================================
    // RESPUESTA
    // ========================================================

    return res.status(201).json({
      success: true,

      message:
        "Trabajo de análisis creado correctamente.",

      repository: {
        id: repository.id,
        fullName:
          repository.full_name,
      },

      job,
    });
  } catch (error) {
    console.error(
      "Error creando job:",
      error
    );

    return res.status(500).json({
      success: false,
      error:
        "No se pudo crear el trabajo de análisis.",
    });
  }
}