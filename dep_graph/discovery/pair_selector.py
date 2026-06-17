from itertools import combinations


class PairSelector:

   
    EXCLUDED_SUFFIXES=(
        "_pct",
        "_mix"
    )
    
    EXCLUDED_COLUMNS = {
    "effective_price",
    "fulfilled_orders",
    "subcategory",
    "category",
    "brand"
    }


    def should_skip(
        self,
        column_name: str
    ) -> bool:

        column_name = column_name.lower()

            
        for suff in self.EXCLUDED_SUFFIXES:
            if column_name.endswith(suff):
                return True
            
        for col in self.EXCLUDED_COLUMNS:
            
            if column_name == col:
                return True
            
        return False

    def generate_pairs(
        self,
        feature_types: dict
    ):

        pairs = []

        valid_columns = [

            col

            for col, dtype in feature_types.items()

            if dtype not in (
                "identifier",
                "temporal"
            )
            

            and not self.should_skip(col)
        ]

        for col1, col2 in combinations(
            valid_columns,
            2
        ):

            type1 = feature_types[col1]
            type2 = feature_types[col2]

            if (
                type1 == "numerical"
                and type2 == "numerical"
            ):
                pair_type = "num_num"

            elif (
                type1 == "categorical"
                and type2 == "categorical"
            ):
                pair_type = "cat_cat"

            else:
                pair_type = "cat_num"

            pairs.append(
                (
                    col1,
                    col2,
                    pair_type
                )
            )

        return pairs