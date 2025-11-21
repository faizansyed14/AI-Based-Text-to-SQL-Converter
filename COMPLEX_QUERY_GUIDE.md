# Guide: How to Ask for Complex Multi-Table Queries

## Overview
This guide explains how to ask natural language questions that will generate complex SQL queries with multiple table joins, calculated columns, and conditional logic.

## Example Complex Query Breakdown

The query you showed:
```sql
SELECT 
  sa_pr_code PRODUCT_CODE,
  PT_DESC PRODUCT_TAG,
  pr_desc DESCRIPTION,
  sa_stock_qty stock_qty,
  pr_free_qty free_qty,
  sa_unit_cost unit_price,
  sa_stock_qty * sa_unit_cost AS Total_Value,
  br_desc brand
FROM 
  str_stock_age,
  edc_product,
  edc_brand,
  edc_product_tag 
WHERE 
  sa_pr_code = pr_code 
  AND substr(pr_code, 1, 3) = br_code 
  AND PT_CODE = PR_PT_CODE 
  ...
```

## How to Ask for This Query in Natural Language

### Option 1: Describe What You Want to See
**Ask:** 
> "Show me stock age data with product code, product tag description, product description, stock quantity, free quantity, unit cost, total value (stock qty times unit cost), and brand description"

### Option 2: Break Down the Requirements
**Ask:**
> "I need a report showing:
> - Product code from stock age table
> - Product tag description
> - Product description
> - Stock quantity and free quantity
> - Unit cost and total value (calculated as stock qty * unit cost)
> - Brand description
> Join stock age with products, brands, and product tags"

### Option 3: Use Business Language
**Ask:**
> "Show me all stock aging information with product details, brand, and product tags. Include calculated total value for each item."

## Key Phrases That Help Generate Complex Queries

### For Joins:
- "with [table name]" - e.g., "products with brands"
- "including [table name]" - e.g., "stock data including product details"
- "join [table]" - e.g., "join products and brands"
- "combine [table1] and [table2]" - e.g., "combine stock age and products"

### For Calculated Columns:
- "calculate [formula]" - e.g., "calculate total value as stock qty times unit cost"
- "multiply [col1] by [col2]" - e.g., "multiply stock quantity by unit cost"
- "total value" - system will calculate if you mention it
- "as [alias]" - e.g., "show total as Total_Value"

### For Conditional Logic:
- "where [condition]" - e.g., "where age days is less than 45"
- "filter by [condition]" - e.g., "filter by division code"
- "only show [condition]" - e.g., "only show items where stock qty is greater than 0"
- "age between X and Y" - e.g., "age between 45 and 90 days"

### For String Matching:
- "first 3 characters" - e.g., "where first 3 characters of product code equals brand code"
- "starting with" - e.g., "product codes starting with 'ABC'"
- "contains" - e.g., "brand description contains 'SAS'"

## Best Practices

1. **Be Specific About Tables**: Mention which tables you want to combine
   - ✅ "Show stock age with product and brand information"
   - ❌ "Show everything"

2. **Mention Calculated Fields**: Explicitly state if you want calculations
   - ✅ "Calculate total value as stock quantity multiplied by unit cost"
   - ❌ "Show total" (ambiguous)

3. **Specify Join Conditions**: If you know the relationship, mention it
   - ✅ "Join products to brands where first 3 characters of product code equals brand code"
   - ❌ "Join products and brands" (system will try to find common columns)

4. **Use Business Terms**: The system understands business terminology
   - ✅ "Show stock aging report with product details"
   - ✅ "List products with their brand and category"
   - ✅ "Calculate total inventory value"

5. **Break Down Complex Requirements**: For very complex queries, break it into parts
   - ✅ "Show stock age data. Include product code, description, stock quantity, unit cost, and brand. Calculate total value as stock qty times unit cost."

## Common Complex Query Patterns

### Pattern 1: Multi-Table Report
**Question:** "Show me a report with products, their brands, categories, and stock information"

**Generated SQL will:**
- Join EDC_PRODUCT, EDC_BRAND, EDC_CATEGORY, STR_STOCK_CARD
- Match by common codes/IDs
- Return relevant columns from each table

### Pattern 2: Calculated Metrics
**Question:** "Calculate total inventory value by multiplying stock quantity by unit cost for each product"

**Generated SQL will:**
- Join stock and product tables
- Calculate: stock_qty * unit_cost AS Total_Value
- Group by product if needed

### Pattern 3: Conditional Filtering
**Question:** "Show stock items where age is less than 45 days, or between 45 and 90 days, or greater than 180 days"

**Generated SQL will:**
- Use WHERE with OR conditions
- Apply date calculations (DATEDIFF)
- Filter based on age ranges

### Pattern 4: Partial String Matching
**Question:** "Show products where the first 3 characters of product code match brand code"

**Generated SQL will:**
- Use SUBSTRING(PR_CODE, 1, 3) = BR_CODE
- Join products and brands accordingly

## Tips for Better Results

1. **Start Simple, Then Add Complexity**: 
   - First: "Show products with brands"
   - Then: "Add stock quantity and calculate total value"

2. **Use Column Descriptions**: The system understands column meanings from descriptions
   - "Show selling price" will find PR_SELLING_PRICE
   - "Show product description" will find PR_DESC

3. **Mention Relationships**: If you know how tables relate, mention it
   - "Join products to categories using category code"
   - "Match products to brands by first 3 characters of product code"

4. **Be Explicit About Calculations**:
   - "Calculate total as quantity times price"
   - "Show average age in days"
   - "Sum all stock quantities"

## Example Questions That Generate Complex Queries

1. **Multi-table with calculations:**
   > "Show me stock age information with product code, product description, brand, stock quantity, unit cost, and calculate total value as stock quantity multiplied by unit cost"

2. **With conditional filtering:**
   > "List all products with their brands and categories, but only show items where the first 3 characters of product code match the brand code, and filter by division code if provided"

3. **With age-based conditions:**
   > "Show stock aging data where age is less than 45 days, or between 45-90 days, or greater than 180 days, including product details and brand information"

4. **Complex aggregation:**
   > "Calculate total inventory value by brand, showing brand name, total stock quantity, average unit cost, and total value (sum of stock qty times unit cost)"

## Troubleshooting

If the generated query doesn't match what you want:

1. **Be More Specific**: Add more details about tables and columns
2. **Break It Down**: Ask for parts separately, then combine
3. **Use Exact Terms**: Use the exact table/column names if you know them
4. **Clarify Relationships**: Explain how tables should be joined
5. **Specify Calculations**: Explicitly state the formula you want

## Advanced: Parameterized Queries

For queries with parameters (like P_DIV_CODE, P_DATE, P_BR_CODE in your example):

**Ask:**
> "Show stock age report filtered by division code (if provided), date (if provided, otherwise use today), and brand code (if provided). Include conditional age filtering based on age days."

The system will generate queries with ISNULL() or COALESCE() for optional parameters.






