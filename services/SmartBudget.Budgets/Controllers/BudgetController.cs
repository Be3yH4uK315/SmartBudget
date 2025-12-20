using Microsoft.AspNetCore.Mvc;
using System.Text.Json;
using SmartBudget.Budgets.Domain.Entities;
using SmartBudget.Budgets.Services;
using SmartBudget.Budgets.DTO;
using Microsoft.EntityFrameworkCore.Diagnostics;

namespace SmartBudget.Budgets.Controllers
{
    [ApiController]
    [Route("api/v1/budget")]
    public class BudgetController : ControllerBase
    {
        private readonly IBudgetService _service;

        public BudgetController(IBudgetService service)
        {
            _service = service;
        }

        /// <summary>
        /// GET Budget info
        /// </summary>
        [HttpGet]
        public async Task<IActionResult> List([FromHeader(Name = "X-User-Id")] Guid userId, CancellationToken stoppingToken = default)
        {
            var budget = await _service.GetBudgetWithCategoriesAsync(userId, stoppingToken);

            if (budget == null)
                return NotFound();

            return Ok(new
            {
                totalLimit = budget.Limit,
                currentValue = budget.CategoryLimits.Sum(cl => cl.Spent),
                isAutoRenew = budget.IsAutoRenew,
                categories = budget.CategoryLimits.Select(cl => new
                {
                    categoryId = cl.CategoryId,
                    limit = cl.Limit,
                    currentValue = cl.Spent
                })
            });
        }
        /// <summary>
        /// GET Budget info
        /// </summary>
        [HttpGet("settings")]
        public async Task<IActionResult> Settings([FromHeader(Name = "X-User-Id")] Guid userId, CancellationToken stoppingToken = default)
        {
            var budget = await _service.GetBudgetSettingsAsync(userId, stoppingToken);

            if (budget == null)
                return NotFound();

            return Ok(new
            {
                totalLimit = budget.Limit,
                isAutoRenew = budget.IsAutoRenew,
                categories = budget.CategoryLimits.Select(cl => new
                {
                    categoryId = cl.CategoryId,
                    limit = cl.Limit,
                })
            });
        }

        /// <summary>
        /// Create Budget 
        /// </summary>
        [HttpPost]
        public async Task<IActionResult> Create([FromHeader(Name = "X-User-Id")] Guid userId, [FromBody] CreateBudgetRequest request, CancellationToken stoppingToken)
        {
            var now = DateTime.UtcNow;

            var budgetId = Guid.NewGuid();
            var budget = new Budget
            {
                Id = budgetId,
                UserId = userId,
                Month = new DateTime(now.Year, now.Month, 1, 0, 0, 0, DateTimeKind.Utc),
                Limit = request.TotalLimit ?? 0,
                IsAutoRenew = request.IsAutoRenew,
                CreatedAt = now,
                UpdatedAt = now,
                CategoryLimits = request.Categories.Select(c => new CategoryLimit
                {
                    Id = Guid.NewGuid(),
                    BudgetId = budgetId, 
                    CategoryId = c.CategoryId,
                    Limit = c.Limit,
                    Spent = 0,
                    CreatedAt = now,
                    UpdatedAt = now
                }).ToList()
            };



            return Ok(await _service.CreateBudgetAsync(budget, stoppingToken));
        }

        [HttpPatch("settings")]
        public async Task<IActionResult> Patch([FromHeader(Name = "X-User-Id")] Guid userId, [FromBody] PatchBudgetRequest request, CancellationToken stoppingToken)
        {
            var model = new PatchBudgetRequest
            {
                TotalLimit = request.TotalLimit,
                IsAutoRenew = request.IsAutoRenew,
                Categories = request.Categories
                    .Select(c => new PatchCategoryLimitRequest
                    {
                        CategoryId = c.CategoryId,
                        Limit = c.Limit
                    })
                    .ToList()
            };
            if (userId == Guid.Empty)
            {
                return BadRequest("X-User-Id header is missing or invalid");
            }

            var budget = await _service.PatchBudgetAsync(userId, model, stoppingToken);

            if (budget == null)
                return NotFound();

            return Ok();
        }
        /// <summary>
        /// Health check endpoint
        /// </summary>
        [HttpGet("health")]
        public IActionResult Health()
        {
            return Ok(new { status = "Healthy" });
        }
    }
}