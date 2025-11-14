import './QueryExamples.css'

interface QueryExample {
  category: string
  question: string
  tip: string
  complexity: 'simple' | 'intermediate' | 'complex'
}

const QUERY_EXAMPLES: QueryExample[] = [
  // Simple Queries - Single Table
  {
    category: 'Basic Data Retrieval',
    question: 'Show me all brands',
    tip: 'Retrieves all brand codes and descriptions from EDC_BRAND table',
    complexity: 'simple'
  },
  {
    category: 'Basic Data Retrieval',
    question: 'List all products',
    tip: 'Shows complete product information including codes, descriptions, and prices',
    complexity: 'simple'
  },
  {
    category: 'Basic Data Retrieval',
    question: 'Display all categories',
    tip: 'Get a list of all product categories with codes and descriptions',
    complexity: 'simple'
  },
  {
    category: 'Basic Data Retrieval',
    question: 'Show me all stock card transactions',
    tip: 'Retrieves all stock movement records from STR_STOCK_CARD',
    complexity: 'simple'
  },
  {
    category: 'Basic Data Retrieval',
    question: 'List all products with their codes and descriptions',
    tip: 'Shows product codes and descriptions only',
    complexity: 'simple'
  },
  {
    category: 'Basic Data Retrieval',
    question: 'Show me all brands with their codes',
    tip: 'Displays brand codes and descriptions',
    complexity: 'simple'
  },

  // Filtering Queries
  {
    category: 'Filtering & Search',
    question: 'Find all products where selling price is greater than 1000',
    tip: 'Filters products by price threshold using PR_SELLING_PRICE',
    complexity: 'simple'
  },
  {
    category: 'Filtering & Search',
    question: 'Show me products with brand code 899',
    tip: 'Filters products by specific brand code (899 = SAS)',
    complexity: 'simple'
  },
  {
    category: 'Filtering & Search',
    question: 'Find products where price is between 200 and 1000',
    tip: 'Range filtering using BETWEEN operator on PR_SELLING_PRICE',
    complexity: 'intermediate'
  },
  {
    category: 'Filtering & Search',
    question: 'Show me all products in category DAVIDSON',
    tip: 'Filters by category description using CT_DESC',
    complexity: 'simple'
  },
  {
    category: 'Filtering & Search',
    question: 'Find products where stock on hand is greater than 0',
    tip: 'Identifies products that are currently in stock',
    complexity: 'simple'
  },
  {
    category: 'Filtering & Search',
    question: 'Show me products that contain "CPU" in the description',
    tip: 'Text search using LIKE pattern matching on PR_DESC',
    complexity: 'simple'
  },
  {
    category: 'Filtering & Search',
    question: 'Find all products created after year 2000',
    tip: 'Date filtering on PR_CREATED_DATE column',
    complexity: 'intermediate'
  },
  {
    category: 'Filtering & Search',
    question: 'Show me products where price is greater than 500 and stock is greater than 100',
    tip: 'Multiple conditions with AND operator',
    complexity: 'intermediate'
  },
  {
    category: 'Filtering & Search',
    question: 'Find products with PR_ADDF_CODE starting with CMQ',
    tip: 'Pattern matching for additional product codes',
    complexity: 'simple'
  },
  {
    category: 'Filtering & Search',
    question: 'Show me products where PR_ADDF_CODE is CMQ/LAPT',
    tip: 'Exact match search for specific additional code',
    complexity: 'simple'
  },
  {
    category: 'Filtering & Search',
    question: 'Find all products with brand SAS',
    tip: 'Filters products by brand description (SAS)',
    complexity: 'simple'
  },
  {
    category: 'Filtering & Search',
    question: 'Show me products where PR_ADDF_CODE contains LAPT',
    tip: 'Searches for products with laptop-related codes',
    complexity: 'simple'
  },

  // Complex Filtering
  {
    category: 'Advanced Filtering',
    question: 'Find all products where price is between 200 and 1000, brand is SAS, and stock is greater than 0',
    tip: 'Multiple filters across price, brand, and stock columns',
    complexity: 'complex'
  },
  {
    category: 'Advanced Filtering',
    question: 'Show me products where brand is either SAS or QUEST SOFTWARE',
    tip: 'Multiple value filtering using IN or OR with brand descriptions',
    complexity: 'intermediate'
  },
  {
    category: 'Advanced Filtering',
    question: 'Find products that have zero stock on hand',
    tip: 'Filtering for zero or null stock values',
    complexity: 'simple'
  },
  {
    category: 'Advanced Filtering',
    question: 'Show me all products except those with brand code 899',
    tip: 'Exclusion filtering using NOT or != operator',
    complexity: 'intermediate'
  },
  {
    category: 'Advanced Filtering',
    question: 'Find products where PR_ADDF_CODE is SKY/CPU or SKY/MBD',
    tip: 'Multiple value filtering for additional codes',
    complexity: 'intermediate'
  },
  {
    category: 'Advanced Filtering',
    question: 'Show me products with price above 1000 and category is DIGITAL INTEGRATION',
    tip: 'Combines price and category filters',
    complexity: 'intermediate'
  },

  // Aggregation Queries
  {
    category: 'Counting & Aggregation',
    question: 'How many products are there?',
    tip: 'Counts total number of products in EDC_PRODUCT table',
    complexity: 'simple'
  },
  {
    category: 'Counting & Aggregation',
    question: 'How many stock card transactions are there?',
    tip: 'Counts total transactions in STR_STOCK_CARD',
    complexity: 'simple'
  },
  {
    category: 'Counting & Aggregation',
    question: 'What is the total stock on hand for all products?',
    tip: 'Sums PR_STOCK_ONHAND across all products',
    complexity: 'simple'
  },
  {
    category: 'Counting & Aggregation',
    question: 'What is the average selling price of all products?',
    tip: 'Calculates average of PR_SELLING_PRICE column',
    complexity: 'simple'
  },
  {
    category: 'Counting & Aggregation',
    question: 'What is the highest selling price?',
    tip: 'Finds maximum value in PR_SELLING_PRICE',
    complexity: 'simple'
  },
  {
    category: 'Counting & Aggregation',
    question: 'What is the lowest selling price?',
    tip: 'Finds minimum value in PR_SELLING_PRICE',
    complexity: 'simple'
  },
  {
    category: 'Counting & Aggregation',
    question: 'How many products does each brand have?',
    tip: 'Grouped counting with GROUP BY on brand code',
    complexity: 'intermediate'
  },
  {
    category: 'Counting & Aggregation',
    question: 'What is the total stock on hand for each brand?',
    tip: 'Sum aggregation of stock grouped by brand',
    complexity: 'intermediate'
  },
  {
    category: 'Counting & Aggregation',
    question: 'What is the average price for each brand?',
    tip: 'Average calculation per brand using GROUP BY',
    complexity: 'intermediate'
  },
  {
    category: 'Counting & Aggregation',
    question: 'Show me the total quantity in stock for each category',
    tip: 'Sum aggregation of stock grouped by category',
    complexity: 'intermediate'
  },
  {
    category: 'Counting & Aggregation',
    question: 'How many products have stock greater than 0?',
    tip: 'Counts products with available inventory',
    complexity: 'simple'
  },
  {
    category: 'Counting & Aggregation',
    question: 'What is the total value of all products in stock?',
    tip: 'Calculates sum of (stock * price) for inventory value',
    complexity: 'intermediate'
  },
  {
    category: 'Counting & Aggregation',
    question: 'How many stock transactions of each type are there?',
    tip: 'Groups and counts by SCD_TRANSACTION_TYPE',
    complexity: 'intermediate'
  },

  // JOIN Queries
  {
    category: 'Multi-Table Queries',
    question: 'Show me all products with their brand names',
    tip: 'JOINs EDC_PRODUCT with EDC_BRAND to show brand descriptions',
    complexity: 'intermediate'
  },
  {
    category: 'Multi-Table Queries',
    question: 'List products with their category descriptions',
    tip: 'JOINs EDC_PRODUCT with EDC_CATEGORY to show category names',
    complexity: 'intermediate'
  },
  {
    category: 'Multi-Table Queries',
    question: 'Show me all products with their brand names and category descriptions',
    tip: 'Multiple JOINs across EDC_PRODUCT, EDC_BRAND, and EDC_CATEGORY tables',
    complexity: 'complex'
  },
  {
    category: 'Multi-Table Queries',
    question: 'Display stock card transactions with product descriptions',
    tip: 'JOINs STR_STOCK_CARD with EDC_PRODUCT for product details',
    complexity: 'intermediate'
  },
  {
    category: 'Multi-Table Queries',
    question: 'Show me products with brand and category information and prices',
    tip: 'Complex multi-table JOIN with all product details',
    complexity: 'complex'
  },
  {
    category: 'Multi-Table Queries',
    question: 'List stock transactions with product codes, descriptions, and transaction types',
    tip: 'JOINs stock card with product table for comprehensive view',
    complexity: 'intermediate'
  },
  {
    category: 'Multi-Table Queries',
    question: 'Show me products with brand SAS and their stock quantities',
    tip: 'JOINs products with brands and filters by brand',
    complexity: 'intermediate'
  },

  // Top N Queries
  {
    category: 'Top & Ranking',
    question: 'What are the top 10 products by selling price?',
    tip: 'Orders by PR_SELLING_PRICE descending and limits to 10',
    complexity: 'simple'
  },
  {
    category: 'Top & Ranking',
    question: 'Show me the top 5 brands by number of products',
    tip: 'Groups by brand, counts products, and ranks results',
    complexity: 'intermediate'
  },
  {
    category: 'Top & Ranking',
    question: 'What are the top 10 products by stock on hand?',
    tip: 'Orders by PR_STOCK_ONHAND descending',
    complexity: 'simple'
  },
  {
    category: 'Top & Ranking',
    question: 'Show me the 5 most expensive products',
    tip: 'Orders descending by PR_SELLING_PRICE and limits to 5',
    complexity: 'simple'
  },
  {
    category: 'Top & Ranking',
    question: 'What are the top 3 brands by total stock quantity?',
    tip: 'Aggregates stock by brand and ranks by total',
    complexity: 'intermediate'
  },
  {
    category: 'Top & Ranking',
    question: 'Show me the top 10 products with highest stock value',
    tip: 'Calculates stock * price and orders descending',
    complexity: 'intermediate'
  },
  {
    category: 'Top & Ranking',
    question: 'What are the top 5 categories by number of products?',
    tip: 'Groups by category, counts, and ranks',
    complexity: 'intermediate'
  },

  // Date Queries
  {
    category: 'Date & Time Queries',
    question: 'Show me all products created in year 2000',
    tip: 'Date filtering on PR_CREATED_DATE for specific year',
    complexity: 'intermediate'
  },
  {
    category: 'Date & Time Queries',
    question: 'What are the stock transactions from year 2002?',
    tip: 'Year-based date filtering on SCD_TRANSACTION_DATE',
    complexity: 'intermediate'
  },
  {
    category: 'Date & Time Queries',
    question: 'Display products created between January 1, 2000 and December 31, 2000',
    tip: 'Specific date range filtering on PR_CREATED_DATE',
    complexity: 'intermediate'
  },
  {
    category: 'Date & Time Queries',
    question: 'Show me stock transactions from February 2002',
    tip: 'Month and year filtering on transaction date',
    complexity: 'intermediate'
  },
  {
    category: 'Date & Time Queries',
    question: 'What are the stock transactions from the first week of February 2002?',
    tip: 'Week-based date range filtering',
    complexity: 'intermediate'
  },
  {
    category: 'Date & Time Queries',
    question: 'Show me products created after September 2000',
    tip: 'Date comparison filtering',
    complexity: 'intermediate'
  },

  // Specific Value Search
  {
    category: 'Specific Value Search',
    question: 'Give me the full row whose pr addf code is CMQ/LAPT',
    tip: 'Exact match search for specific PR_ADDF_CODE value',
    complexity: 'simple'
  },
  {
    category: 'Specific Value Search',
    question: 'Find the product with code 206AD ATP3',
    tip: 'Searches by exact PR_CODE value',
    complexity: 'simple'
  },
  {
    category: 'Specific Value Search',
    question: 'Show me the brand with code 899',
    tip: 'Retrieves specific brand record by BR_CODE',
    complexity: 'simple'
  },
  {
    category: 'Specific Value Search',
    question: 'Find all products with PR_ADDF_CODE SKY/CPU',
    tip: 'Filters products by specific additional code',
    complexity: 'simple'
  },
  {
    category: 'Specific Value Search',
    question: 'Show me all stock transactions for product code 503AS AX200458',
    tip: 'Filters stock card by specific product code',
    complexity: 'simple'
  },
  {
    category: 'Specific Value Search',
    question: 'Find products with brand code 786',
    tip: 'Filters products by specific brand code (786 = QUEST SOFTWARE)',
    complexity: 'simple'
  },
  {
    category: 'Specific Value Search',
    question: 'Show me the category with code 314EO',
    tip: 'Retrieves specific category by CT_CODE',
    complexity: 'simple'
  },

  // Statistical Queries
  {
    category: 'Statistics & Analysis',
    question: 'What is the average, minimum, and maximum selling price for each brand?',
    tip: 'Multiple aggregate functions (AVG, MIN, MAX) per brand group',
    complexity: 'complex'
  },
  {
    category: 'Statistics & Analysis',
    question: 'Show me the total stock and average price by brand',
    tip: 'Multiple aggregations (SUM, AVG) grouped by brand',
    complexity: 'complex'
  },
  {
    category: 'Statistics & Analysis',
    question: 'What is the price range for each category?',
    tip: 'Min and max PR_SELLING_PRICE per category',
    complexity: 'intermediate'
  },
  {
    category: 'Statistics & Analysis',
    question: 'Show me the count and total stock value of products per brand',
    tip: 'Count and sum aggregations grouped by brand',
    complexity: 'intermediate'
  },
  {
    category: 'Statistics & Analysis',
    question: 'What is the average stock on hand for each category?',
    tip: 'Average calculation grouped by category',
    complexity: 'intermediate'
  },
  {
    category: 'Statistics & Analysis',
    question: 'Show me the total quantity received and issued for each transaction type',
    tip: 'Sums SCD_RCPT_QTY and SCD_ISSUE_QTY grouped by transaction type',
    complexity: 'intermediate'
  },

  // Complex Business Queries
  {
    category: 'Business Intelligence',
    question: 'What are the top products by stock value?',
    tip: 'Calculates stock * price and ranks products',
    complexity: 'complex'
  },
  {
    category: 'Business Intelligence',
    question: 'Show me products that have price above the average price',
    tip: 'Uses subquery to compare with average selling price',
    complexity: 'complex'
  },
  {
    category: 'Business Intelligence',
    question: 'Which brands have more than 50 products?',
    tip: 'Filtering aggregated results with HAVING clause',
    complexity: 'intermediate'
  },
  {
    category: 'Business Intelligence',
    question: 'Show me brands with average price above 1000',
    tip: 'HAVING clause for aggregate filtering on average price',
    complexity: 'intermediate'
  },
  {
    category: 'Business Intelligence',
    question: 'What is the total stock value by brand?',
    tip: 'Groups products by brand and sums (stock * price)',
    complexity: 'complex'
  },
  {
    category: 'Business Intelligence',
    question: 'Show me products that have stock but price is zero',
    tip: 'Complex condition checking stock and price',
    complexity: 'intermediate'
  },
  {
    category: 'Business Intelligence',
    question: 'Which categories have products with stock greater than 1000?',
    tip: 'Groups by category and filters with HAVING',
    complexity: 'intermediate'
  },
  {
    category: 'Business Intelligence',
    question: 'Show me brands with total stock value above 100000',
    tip: 'Calculates total value per brand and filters with HAVING',
    complexity: 'complex'
  },

  // Sorting Queries
  {
    category: 'Sorting & Ordering',
    question: 'Show me all products sorted by selling price from lowest to highest',
    tip: 'ASC ordering by PR_SELLING_PRICE',
    complexity: 'simple'
  },
  {
    category: 'Sorting & Ordering',
    question: 'List brands alphabetically by description',
    tip: 'Text sorting of BR_DESC in ascending order',
    complexity: 'simple'
  },
  {
    category: 'Sorting & Ordering',
    question: 'Show me products sorted by description and then by price',
    tip: 'Multiple column sorting on PR_DESC and PR_SELLING_PRICE',
    complexity: 'intermediate'
  },
  {
    category: 'Sorting & Ordering',
    question: 'List products sorted by stock on hand from highest to lowest',
    tip: 'DESC ordering by PR_STOCK_ONHAND',
    complexity: 'simple'
  },
  {
    category: 'Sorting & Ordering',
    question: 'Show me stock transactions sorted by date and then by product code',
    tip: 'Multiple column sorting on date and product code',
    complexity: 'intermediate'
  },

  // Union & Combination
  {
    category: 'Combining Results',
    question: 'Show me all products from brand SAS and also all products with price over 5000',
    tip: 'UNION of two different queries',
    complexity: 'complex'
  },
  {
    category: 'Combining Results',
    question: 'List all products that are either in DAVIDSON category or have price above 1000',
    tip: 'OR condition across different criteria',
    complexity: 'intermediate'
  },
  {
    category: 'Combining Results',
    question: 'Show me products with PR_ADDF_CODE starting with CMQ or SKY',
    tip: 'Multiple pattern matching with OR condition',
    complexity: 'intermediate'
  },

  // Stock Card Specific Queries
  {
    category: 'Stock Transactions',
    question: 'Show me all Cash Invoice transactions',
    tip: 'Filters stock card by SCD_TRANSACTION_TYPE',
    complexity: 'simple'
  },
  {
    category: 'Stock Transactions',
    question: 'Find stock transactions for product 503AS AX200458',
    tip: 'Filters by specific product code in stock card',
    complexity: 'simple'
  },
  {
    category: 'Stock Transactions',
    question: 'Show me all Service Returns transactions',
    tip: 'Filters by transaction type Service Returns',
    complexity: 'simple'
  },
  {
    category: 'Stock Transactions',
    question: 'What is the total quantity received for each product?',
    tip: 'Sums SCD_RCPT_QTY grouped by product code',
    complexity: 'intermediate'
  },
  {
    category: 'Stock Transactions',
    question: 'What is the total quantity issued for each product?',
    tip: 'Sums SCD_ISSUE_QTY grouped by product code',
    complexity: 'intermediate'
  },
  {
    category: 'Stock Transactions',
    question: 'Show me stock transactions with party name NORDX',
    tip: 'Filters by SCD_PARTY_NAME containing NORDX',
    complexity: 'simple'
  },
  {
    category: 'Stock Transactions',
    question: 'Find transactions where receipt quantity is greater than 100',
    tip: 'Filters stock card by receipt quantity threshold',
    complexity: 'simple'
  },
  {
    category: 'Stock Transactions',
    question: 'Show me transactions grouped by transaction type with counts',
    tip: 'Groups by transaction type and counts records',
    complexity: 'intermediate'
  }
]

const QueryExamples = ({ onQuestionClick }: { onQuestionClick: (question: string) => void }) => {
  const categories = Array.from(new Set(QUERY_EXAMPLES.map(q => q.category)))
  
  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'simple': return '#76B900'
      case 'intermediate': return '#FFA500'
      case 'complex': return '#FF4444'
      default: return '#76B900'
    }
  }

  const getComplexityLabel = (complexity: string) => {
    switch (complexity) {
      case 'simple': return 'Easy'
      case 'intermediate': return 'Medium'
      case 'complex': return 'Advanced'
      default: return 'Easy'
    }
  }

  return (
    <div className="query-examples">
      <div className="examples-header">
        <div className="header-icon">💡</div>
        <div>
          <h2>Query Examples & Tips</h2>
          <p>Click any question to use it. {QUERY_EXAMPLES.length} example queries covering all query types.</p>
        </div>
      </div>

      <div className="examples-categories">
        {categories.map(category => {
          const categoryExamples = QUERY_EXAMPLES.filter(q => q.category === category)
          return (
            <div key={category} className="example-category">
              <h3 className="category-title">{category}</h3>
              <div className="examples-grid">
                {categoryExamples.map((example, idx) => (
                  <div
                    key={idx}
                    className="example-card"
                    onClick={() => onQuestionClick(example.question)}
                  >
                    <div className="example-header">
                      <span 
                        className="complexity-badge"
                        style={{ backgroundColor: getComplexityColor(example.complexity) }}
                      >
                        {getComplexityLabel(example.complexity)}
                      </span>
                    </div>
                    <div className="example-question">{example.question}</div>
                    <div className="example-tip">
                      <span className="tip-label">Tip:</span> {example.tip}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default QueryExamples

