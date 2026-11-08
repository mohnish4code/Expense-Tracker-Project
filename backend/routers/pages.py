from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.auth import optional_user
from expense_tracker.config import CATEGORIES, PAYMENT_METHODS

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
templates = Jinja2Templates(directory=FRONTEND_DIR / "templates")

router = APIRouter(include_in_schema=False)


def render(request, name, user, **context):
    return templates.TemplateResponse(
        request,
        name,
        {"user": user, "categories": CATEGORIES, "payment_methods": PAYMENT_METHODS, **context},
    )


def signed_in_page(name, active):
    def handler(request: Request, user=Depends(optional_user)):
        if user is None:
            return RedirectResponse("/login", status_code=303)
        return render(request, name, user, active=active)

    return handler


def auth_page(mode):
    def handler(request: Request, user=Depends(optional_user)):
        if user is not None:
            return RedirectResponse("/", status_code=303)
        return render(request, "login.html", None, mode=mode)

    return handler


router.add_api_route("/", signed_in_page("dashboard.html", "dashboard"), methods=["GET"])
router.add_api_route("/expenses", signed_in_page("expenses.html", "expenses"), methods=["GET"])
router.add_api_route("/budgets", signed_in_page("budgets.html", "budgets"), methods=["GET"])
router.add_api_route("/login", auth_page("login"), methods=["GET"])
router.add_api_route("/register", auth_page("register"), methods=["GET"])
