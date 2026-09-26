import {
  Router,
} from "express";

import {
  createJob,
} from "../controllers/job.controller.js";

import {
  requireAuth,
} from "../middleware/requireAuth.js";

const router = Router();

// POST /api/v1/jobs
router.post(
  "/",
  requireAuth,
  createJob
);

export default router;