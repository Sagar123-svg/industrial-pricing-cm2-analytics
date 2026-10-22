-- ============================================================
-- Industrial Spare Parts Pricing & CM2 Profitability Analytics
-- SCHEMA: Star Schema (MySQL syntax)
-- ============================================================

-- ============================================
-- DIMENSION TABLES
-- ============================================

CREATE TABLE Dim_Material (
    Material_ID           VARCHAR(10) PRIMARY KEY,
    Material_Description  VARCHAR(100),
    Material_Category     VARCHAR(50),
    Material_Subcategory  VARCHAR(50),
    Unit_of_Measure        VARCHAR(10),
    Standard_Cost_Current  DECIMAL(10,2),
    Criticality            VARCHAR(20),
    Introduced_Date        DATE
);

CREATE TABLE Dim_Customer (
    Customer_ID       VARCHAR(10) PRIMARY KEY,
    Customer_Name     VARCHAR(100),
    Customer_Segment  VARCHAR(30),
    Region            VARCHAR(30),
    Customer_Since    DATE
);

CREATE TABLE Dim_Sales_Organization (
    Sales_Org_ID          VARCHAR(10) PRIMARY KEY,
    Sales_Org_Name        VARCHAR(50),
    Country               VARCHAR(30),
    Distribution_Channel  VARCHAR(30),
    Plant                 VARCHAR(20)
);

CREATE TABLE Dim_Pricing_Condition (
    Pricing_Condition_ID   VARCHAR(10) PRIMARY KEY,
    Condition_Type         VARCHAR(30),
    Condition_Description  VARCHAR(100),
    Condition_Value_Type   VARCHAR(20)
);

CREATE TABLE Dim_Date (
    Date         DATE PRIMARY KEY,
    Year         INT,
    Quarter      VARCHAR(2),
    Month        INT,
    Month_Name   VARCHAR(15),
    Week         INT,
    Fiscal_Year  VARCHAR(10)
);

-- Normalized lookup table: category-level target margins.
-- Kept separate from Fact_Sales so the target is maintained in ONE place,
-- not duplicated across thousands of transaction rows.
CREATE TABLE Dim_Category_Target (
    Material_Category     VARCHAR(50) PRIMARY KEY,
    Target_CM2_Percentage DECIMAL(5,2)
);

-- ============================================
-- FACT TABLES
-- ============================================

CREATE TABLE Fact_Sales (
    Transaction_ID                VARCHAR(15) PRIMARY KEY,
    Quote_ID                      VARCHAR(15),
    Order_ID                      VARCHAR(15),
    Material_ID                   VARCHAR(10),
    Customer_ID                   VARCHAR(10),
    Sales_Org_ID                  VARCHAR(10),
    Pricing_Condition_ID          VARCHAR(10),
    Transaction_Date              DATE,
    Quote_Status                  VARCHAR(20),
    Quantity                      INT,
    Standard_Cost                 DECIMAL(10,2),
    List_Price                    DECIMAL(10,2),
    Previous_Price                DECIMAL(10,2),
    Selling_Price                 DECIMAL(10,2),
    Discount_Percentage           DECIMAL(5,2),
    Currency                      VARCHAR(5),
    Revenue                       DECIMAL(12,2),
    Cost                          DECIMAL(12,2),
    CM2                           DECIMAL(12,2),
    CM2_Percentage                DECIMAL(5,2),
    Target_CM2_Percentage         DECIMAL(5,2),
    Negative_CM2_Flag             VARCHAR(3),
    Low_Margin_Flag               VARCHAR(3),
    Price_Revision_Required_Flag  VARCHAR(3),

    CONSTRAINT fk_sales_material  FOREIGN KEY (Material_ID)  REFERENCES Dim_Material(Material_ID),
    CONSTRAINT fk_sales_customer  FOREIGN KEY (Customer_ID)  REFERENCES Dim_Customer(Customer_ID),
    CONSTRAINT fk_sales_salesorg  FOREIGN KEY (Sales_Org_ID) REFERENCES Dim_Sales_Organization(Sales_Org_ID),
    CONSTRAINT fk_sales_condition FOREIGN KEY (Pricing_Condition_ID) REFERENCES Dim_Pricing_Condition(Pricing_Condition_ID),
    CONSTRAINT fk_sales_date      FOREIGN KEY (Transaction_Date) REFERENCES Dim_Date(Date)
);

CREATE TABLE Fact_Pricing (
    Price_Event_ID           VARCHAR(15) PRIMARY KEY,
    Material_ID               VARCHAR(10),
    Change_Date               DATE,
    Change_Type                VARCHAR(20),
    Previous_Price            DECIMAL(10,2),
    New_Price                 DECIMAL(10,2),
    Price_Change_Percentage   DECIMAL(5,2),
    Previous_Cost             DECIMAL(10,2),
    New_Cost                  DECIMAL(10,2),
    Cost_Change_Percentage    DECIMAL(5,2),
    Reason_Code                VARCHAR(30),

    CONSTRAINT fk_pricing_material FOREIGN KEY (Material_ID) REFERENCES Dim_Material(Material_ID),
    CONSTRAINT fk_pricing_date     FOREIGN KEY (Change_Date) REFERENCES Dim_Date(Date)
);
